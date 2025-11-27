#!/usr/bin/env python3

"""
Script to manually update order statuses for demonstration purposes
"""

import json
import os
import sys

# Available statuses
STATUSES = ["received", "confirmed", "being_prepared", "out_for_delivery", "delivered"]

def update_order_status(order_id=None, new_status=None):
    print("Updating order status...")
    
    # Define the path to the order history file
    order_history_file = os.path.join(os.path.dirname(__file__), "data", "order_history.json")
    
    # Check if the file exists
    if not os.path.exists(order_history_file):
        print(f"Error: Order history file not found at {order_history_file}")
        return 1
    
    # Load the order history
    try:
        with open(order_history_file, "r") as f:
            order_history = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in order history file: {e}")
        return 1
    except Exception as e:
        print(f"Error: Failed to load order history: {e}")
        return 1
    
    # If no order ID provided, show available orders
    if not order_id:
        if not order_history:
            print("No orders found in history.")
            return 0
        
        print("\nAvailable orders:")
        for i, order in enumerate(order_history[-5:], 1):  # Show last 5 orders
            print(f"{i}. {order.get('order_id', 'N/A')} - {order.get('status', 'N/A')} - ${order.get('total', 0):.2f}")
        
        print("\nTo update an order, run: python update_order_status.py <order_id> <new_status>")
        print(f"Available statuses: {', '.join(STATUSES)}")
        return 0
    
    # Validate status
    if new_status not in STATUSES:
        print(f"Error: Invalid status '{new_status}'. Available statuses: {', '.join(STATUSES)}")
        return 1
    
    # Find and update the order
    order_found = False
    for order in order_history:
        if order.get("order_id") == order_id:
            old_status = order.get("status", "unknown")
            order["status"] = new_status
            order_found = True
            print(f"Updated order {order_id} from '{old_status}' to '{new_status}'")
            break
    
    if not order_found:
        print(f"Error: Order with ID '{order_id}' not found")
        return 1
    
    # Save the updated order history
    try:
        with open(order_history_file, "w") as f:
            json.dump(order_history, f, indent=2)
        print("Order history updated successfully!")
        return 0
    except Exception as e:
        print(f"Error: Failed to save order history: {e}")
        return 1

if __name__ == "__main__":
    # Parse command line arguments
    order_id = sys.argv[1] if len(sys.argv) > 1 else None
    new_status = sys.argv[2] if len(sys.argv) > 2 else None
    
    exit(update_order_status(order_id, new_status))