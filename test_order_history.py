#!/usr/bin/env python3

"""
Script to test the order history functionality
"""

import json
import os

def test_order_history():
    print("Testing order history functionality...")
    
    # Define the path to the order history file
    order_history_file = os.path.join(os.path.dirname(__file__), "data", "order_history.json")
    
    # Check if the file exists
    if not os.path.exists(order_history_file):
        print(f"Error: Order history file not found at {order_history_file}")
        return 1
    
    # Try to load the JSON data
    try:
        with open(order_history_file, "r") as f:
            order_history = json.load(f)
        
        if isinstance(order_history, list):
            print(f"Successfully loaded order history with {len(order_history)} orders.")
            
            if len(order_history) > 0:
                print("\nMost recent order:")
                latest_order = order_history[-1]
                print(f"  Order ID: {latest_order.get('order_id', 'N/A')}")
                print(f"  Customer: {latest_order.get('customer_name', 'N/A')}")
                print(f"  Status: {latest_order.get('status', 'N/A')}")
                print(f"  Total: ${latest_order.get('total', 0):.2f}")
                print(f"  Items: {len(latest_order.get('items', []))}")
            else:
                print("\nNo orders in history yet.")
            
            print("\nOrder history test completed successfully!")
            return 0
        else:
            print("Error: Order history file does not contain a list.")
            return 1
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in order history file: {e}")
        return 1
    except Exception as e:
        print(f"Error: Failed to load order history: {e}")
        return 1

if __name__ == "__main__":
    exit(test_order_history())