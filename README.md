# Day 7 - Food & Grocery Ordering Voice Agent

This repository contains the implementation of the Food & Grocery Ordering Voice Agent for Day 7 of the 10 Days of Voice Agents challenge.

## Overview

This project implements a food and grocery ordering voice agent that allows users to order items from a catalog using voice commands. The agent can intelligently handle requests like "ingredients for a peanut butter sandwich" by adding multiple related items to the cart. Users can add items, update quantities, remove items, and view their cart during the conversation. When ready, they can place their order which gets saved to a JSON file.

## Features

- Browse and search food/grocery catalog
- Intelligent recipe handling ("ingredients for X" requests)
- Cart management (add, remove, update quantities, view cart)
- Order placement with JSON persistence
- Order history tracking
- Voice-based interaction using LiveKit Agents

## Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend, if needed)
- LiveKit account and credentials
- Deepgram API key
- Google Cloud credentials
- Murf API key

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/adixists/ten-days-of-voice-agents-day7.git
   cd ten-days-of-voice-agents-day7
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   or alternatively:
   ```bash
   pip install livekit-agents livekit-plugins-deepgram livekit-plugins-google livekit-plugins-murf
   ```

## Configuration

1. Copy `.env.example` to `.env.local` and fill in your credentials:
   ```bash
   cp .env.example .env.local
   ```

2. Edit `.env.local` with your actual credentials:
   ```
   LIVEKIT_URL=wss://your-livekit-url
   LIVEKIT_API_KEY=your-api-key
   LIVEKIT_API_SECRET=your-api-secret
   DEEPGRAM_API_KEY=your-deepgram-api-key
   GOOGLE_APPLICATION_CREDENTIALS=path-to-your-google-credentials.json
   MURF_API_KEY=your-murf-api-key
   ```

   You'll need to obtain actual credentials from:
   - [LiveKit Cloud](https://cloud.livekit.io/)
   - [Deepgram Console](https://console.deepgram.com/)
   - [Google Cloud Console](https://console.cloud.google.com/)
   - [Murf AI](https://murf.ai/)

   **Important**: The `.env.local` file is included in `.gitignore` to prevent accidental credential exposure.

## Running the Agent

1. Start the backend agent:
   ```bash
   python run_agent.py
   ```
   or alternatively:
   ```bash
   cd src && python -m agent dev
   ```

2. If you have a frontend, start it in a separate terminal:
   ```bash
   npm run dev
   ```

3. Open your browser to `http://localhost:3000` (or the port shown in the terminal)

## Testing

You can test the food catalog by running:
```bash
python test_catalog.py
```

You can test the order history functionality by running:
```bash
python test_order_history.py
```

You can run a demo of the agent logic without requiring API credentials:
```bash
python demo_agent_logic.py
```

## Catalog Structure

The food catalog is stored in `data/catalog.json` with the following structure:

```json
{
  "categories": {
    "groceries": [...],
    "snacks": [...],
    "prepared_food": [...],
    "beverages": [...]
  },
  "recipes": {
    "peanut_butter_sandwich": {...},
    "pasta_for_two": {...},
    "healthy_breakfast": {...}
  }
}
```

Each item in the catalog has:
- Unique ID
- Name
- Brand
- Price
- Size
- Tags (e.g., "vegan", "gluten-free")

Recipes map to multiple items for common meal preparations.

## Order History

Orders are stored in `data/order_history.json` as a list of order objects. Each order contains:
- Unique order ID
- Customer name
- Timestamp
- Items with quantities and prices
- Total amount
- Delivery notes
- Status

For demonstration purposes, you can manually update order statuses using the provided script:
```bash
python update_order_status.py
```

This will show available orders and instructions for updating their statuses.

## Usage Examples

The agent can handle various user requests:

1. **Browsing items**: "Show me snacks"
2. **Searching**: "I need bread"
3. **Adding items**: "Add 2 loaves of bread to my cart"
4. **Recipe requests**: "I need ingredients for a peanut butter sandwich"
5. **Cart management**: "What's in my cart?", "Remove the chips", "Change the bread quantity to 3"
6. **Placing orders**: "That's all", "Place my order"

## Customization

You can modify the catalog in `data/catalog.json` to:
- Add new items
- Create new categories
- Add more recipes
- Adjust prices

## License

This project is licensed under the MIT License.