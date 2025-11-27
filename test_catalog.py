#!/usr/bin/env python3

"""
Script to test the food catalog
"""

import json
import os

def test_catalog():
    print("Testing food catalog...")
    
    # Define the path to the catalog file
    catalog_file = os.path.join(os.path.dirname(__file__), "data", "catalog.json")
    
    # Check if the file exists
    if not os.path.exists(catalog_file):
        print(f"Error: Catalog file not found at {catalog_file}")
        return 1
    
    # Try to load the JSON data
    try:
        with open(catalog_file, "r") as f:
            catalog = json.load(f)
        
        print("Successfully loaded catalog.")
        
        # Print catalog statistics
        categories = catalog.get("categories", {})
        total_items = 0
        
        for category_name, items in categories.items():
            print(f"\n{category_name.title()}: {len(items)} items")
            total_items += len(items)
            
        print(f"\nTotal items in catalog: {total_items}")
        
        # Print recipes
        recipes = catalog.get("recipes", {})
        print(f"\nAvailable recipes: {len(recipes)}")
        for recipe_key, recipe in recipes.items():
            print(f"  - {recipe['name']}: {recipe['description']}")
            
        print("\nCatalog test completed successfully!")
        return 0
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in catalog file: {e}")
        return 1
    except Exception as e:
        print(f"Error: Failed to load catalog: {e}")
        return 1

if __name__ == "__main__":
    exit(test_catalog())