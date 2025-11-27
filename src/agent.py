import logging
import json
import os
from datetime import datetime
from typing import Annotated, Optional, List, Dict
from collections import defaultdict

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
    tokenize,
    function_tool,
    RunContext
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Load catalog
CATALOG_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.json")
ORDER_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "order_history.json")

def load_catalog():
    try:
        with open(CATALOG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading catalog: {e}")
        return {}

def load_order_history():
    try:
        if os.path.exists(ORDER_HISTORY_FILE):
            with open(ORDER_HISTORY_FILE, "r") as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        logger.error(f"Error loading order history: {e}")
        return []

def save_order_history(order_history):
    try:
        with open(ORDER_HISTORY_FILE, "w") as f:
            json.dump(order_history, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving order history: {e}")
        return False

CATALOG = load_catalog()

class FoodOrderingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a friendly food and grocery ordering assistant for QuickCart, a fictional online grocery store. Your role is to help users order food and groceries from our catalog.

When a call starts:
1. Greet the user warmly and explain what you can help with
2. Help users browse items in our catalog or search for specific items
3. Add items to their cart with quantities
4. Handle special requests like "ingredients for X"
5. Allow users to update quantities, remove items, or view their cart
6. When the user is ready to checkout:
   - Confirm the final cart contents and total
   - Collect any necessary information (name, delivery notes)
   - Place the order and save it to our system

Key behaviors:
- Be friendly, helpful, and conversational
- Ask for clarification when needed (quantities, sizes, brands)
- Confirm all cart changes verbally so users know what's happening
- Handle "ingredients for X" requests by adding multiple related items
- Support cart management (add, remove, update quantities, view cart)
- When placing an order, save it to a JSON file with a timestamp

Catalog categories:
- Groceries (bread, eggs, milk, etc.)
- Snacks (chips, chocolate, nuts)
- Prepared food (pizzas, sandwiches, salads)
- Beverages (juice, coffee)

Special recipe requests:
- "peanut_butter_sandwich" - bread and cheese
- "pasta_for_two" - caesar salad and orange juice
- "healthy_breakfast" - eggs, bananas, and coffee

Be patient and helpful throughout the ordering process!
""",
        )

    @function_tool
    async def search_items(
        self,
        context: RunContext,
        query: Annotated[str, "The user's search query for items"],
    ):
        """Search for items in the catalog that match the user's query.
        
        Args:
            query: The user's search query
        """
        query_lower = query.lower()
        results = []
        
        # Search in all categories
        for category_name, items in CATALOG.get("categories", {}).items():
            for item in items:
                # Check if query matches item name, brand, or tags
                if (query_lower in item["name"].lower() or 
                    query_lower in item.get("brand", "").lower() or
                    any(query_lower in tag.lower() for tag in item.get("tags", []))):
                    results.append({
                        "id": item["id"],
                        "name": item["name"],
                        "category": category_name,
                        "price": item["price"],
                        "size": item["size"],
                        "brand": item.get("brand", ""),
                    })
        
        if results:
            response = f"I found {len(results)} item(s) matching '{query}':\n"
            for item in results[:5]:  # Limit to first 5 results
                response += f"- {item['name']} ({item['brand']}) - ${item['price']} ({item['size']}) [{item['category']}]\n"
            return response
        else:
            return f"I couldn't find any items matching '{query}'. Would you like to try a different search?"

    @function_tool
    async def add_to_cart(
        self,
        context: RunContext,
        item_id: Annotated[str, "The ID of the item to add"],
        quantity: Annotated[int, "The quantity to add"] = 1,
    ):
        """Add an item to the user's cart.
        
        Args:
            item_id: The ID of the item to add
            quantity: The quantity to add (default: 1)
        """
        # Get cart from session or create new one
        cart = context.session_userdata.get("cart", {})
        
        # Find the item in the catalog
        item = None
        category_name = None
        for cat_name, items in CATALOG.get("categories", {}).items():
            for catalog_item in items:
                if catalog_item["id"] == item_id:
                    item = catalog_item
                    category_name = cat_name
                    break
            if item:
                break
        
        if not item:
            return f"Sorry, I couldn't find an item with ID {item_id}."
        
        # Add to cart
        if item_id in cart:
            cart[item_id]["quantity"] += quantity
        else:
            cart[item_id] = {
                "item": item,
                "category": category_name,
                "quantity": quantity
            }
        
        context.session_userdata["cart"] = cart
        
        return f"Added {quantity} x {item['name']} to your cart."

    @function_tool
    async def remove_from_cart(
        self,
        context: RunContext,
        item_id: Annotated[str, "The ID of the item to remove"],
    ):
        """Remove an item from the user's cart.
        
        Args:
            item_id: The ID of the item to remove
        """
        cart = context.session_userdata.get("cart", {})
        
        if item_id in cart:
            removed_item = cart.pop(item_id)
            context.session_userdata["cart"] = cart
            return f"Removed {removed_item['item']['name']} from your cart."
        else:
            return "That item isn't in your cart."

    @function_tool
    async def update_quantity(
        self,
        context: RunContext,
        item_id: Annotated[str, "The ID of the item to update"],
        quantity: Annotated[int, "The new quantity"],
    ):
        """Update the quantity of an item in the user's cart.
        
        Args:
            item_id: The ID of the item to update
            quantity: The new quantity
        """
        cart = context.session_userdata.get("cart", {})
        
        if item_id in cart:
            if quantity <= 0:
                # Remove item if quantity is 0 or negative
                removed_item = cart.pop(item_id)
                context.session_userdata["cart"] = cart
                return f"Removed {removed_item['item']['name']} from your cart."
            else:
                cart[item_id]["quantity"] = quantity
                context.session_userdata["cart"] = cart
                return f"Updated {cart[item_id]['item']['name']} quantity to {quantity}."
        else:
            return "That item isn't in your cart."

    @function_tool
    async def view_cart(self, context: RunContext):
        """View the current contents of the user's cart.
        
        Args:
            None
        """
        cart = context.session_userdata.get("cart", {})
        
        if not cart:
            return "Your cart is currently empty."
        
        total = 0
        response = "Here's what's in your cart:\n"
        
        for item_id, cart_item in cart.items():
            item = cart_item["item"]
            quantity = cart_item["quantity"]
            price = item["price"]
            subtotal = price * quantity
            total += subtotal
            
            response += f"- {quantity} x {item['name']} (${price:.2f} each) = ${subtotal:.2f}\n"
        
        response += f"\nTotal: ${total:.2f}"
        return response

    @function_tool
    async def add_recipe_items(
        self,
        context: RunContext,
        recipe_key: Annotated[str, "The key of the recipe to add"],
    ):
        """Add all items for a recipe to the user's cart.
        
        Args:
            recipe_key: The key of the recipe to add
        """
        recipes = CATALOG.get("recipes", {})
        if recipe_key not in recipes:
            return f"Sorry, I don't have a recipe for '{recipe_key}'."
        
        recipe = recipes[recipe_key]
        item_ids = recipe["items"]
        
        # Add each item to cart
        added_items = []
        for item_id in item_ids:
            # Find the item in the catalog
            item = None
            for cat_name, items in CATALOG.get("categories", {}).items():
                for catalog_item in items:
                    if catalog_item["id"] == item_id:
                        item = catalog_item
                        break
                if item:
                    break
            
            if item:
                # Add to cart (1 quantity each)
                cart = context.session_userdata.get("cart", {})
                if item_id in cart:
                    cart[item_id]["quantity"] += 1
                else:
                    category_name = None
                    for cat_name, items in CATALOG.get("categories", {}).items():
                        if item in items:
                            category_name = cat_name
                            break
                    
                    cart[item_id] = {
                        "item": item,
                        "category": category_name,
                        "quantity": 1
                    }
                
                context.session_userdata["cart"] = cart
                added_items.append(item["name"])
        
        if added_items:
            return f"I've added {', '.join(added_items)} to your cart for your {recipe['name']}."
        else:
            return f"Sorry, I couldn't add items for {recipe['name']}."

    @function_tool
    async def place_order(
        self,
        context: RunContext,
        customer_name: Annotated[Optional[str], "The customer's name"] = None,
        delivery_notes: Annotated[Optional[str], "Any delivery notes"] = None,
    ):
        """Place the order and save it to a JSON file.
        
        Args:
            customer_name: The customer's name
            delivery_notes: Any delivery notes
        """
        cart = context.session_userdata.get("cart", {})
        
        if not cart:
            return "Your cart is empty. Please add some items before placing an order."
        
        # Calculate total
        total = 0
        order_items = []
        
        for item_id, cart_item in cart.items():
            item = cart_item["item"]
            quantity = cart_item["quantity"]
            price = item["price"]
            subtotal = price * quantity
            total += subtotal
            
            order_items.append({
                "id": item_id,
                "name": item["name"],
                "brand": item.get("brand", ""),
                "category": cart_item["category"],
                "price": price,
                "quantity": quantity,
                "subtotal": subtotal
            })
        
        # Create order object
        order = {
            "order_id": f"ORD-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "customer_name": customer_name or "Anonymous Customer",
            "timestamp": datetime.now().isoformat(),
            "items": order_items,
            "total": round(total, 2),
            "delivery_notes": delivery_notes or "",
            "status": "received"
        }
        
        # Load existing order history
        order_history = load_order_history()
        
        # Add new order
        order_history.append(order)
        
        # Save order history
        if save_order_history(order_history):
            # Clear cart
            context.session_userdata["cart"] = {}
            return f"Your order has been placed successfully! Order ID: {order['order_id']}. Total: ${order['total']:.2f}. Thank you for shopping with QuickCart!"
        else:
            return "Sorry, there was an error placing your order. Please try again."

    @function_tool
    async def get_order_status(
        self,
        context: RunContext,
        order_id: Annotated[Optional[str], "The order ID to check"] = None,
    ):
        """Check the status of an order.
        
        Args:
            order_id: The order ID to check (optional)
        """
        order_history = load_order_history()
        
        if not order_history:
            return "You don't have any orders yet."
        
        # If no order ID provided, get the most recent order
        if not order_id:
            latest_order = order_history[-1]
            return f"Your most recent order (ID: {latest_order['order_id']}) is currently {latest_order['status']}."
        
        # Find specific order
        for order in order_history:
            if order["order_id"] == order_id:
                return f"Order {order['order_id']} is currently {order['status']}."
        
        return f"Sorry, I couldn't find an order with ID {order_id}."

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up voice AI pipeline
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Metrics collection
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Initialize cart in session userdata
    session.userdata["cart"] = {}

    # Start the session
    await session.start(
        agent=FoodOrderingAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))