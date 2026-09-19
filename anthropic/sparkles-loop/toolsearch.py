"""Module 2.2: tool search. Sparkles has a growing catalog of tools; instead of
loading all of them into context, Claude searches for the ones it needs.

Pinned to tool_search_tool_bm25_20251119. The tool name is fixed by the API:
it must be "tool_search_tool_bm25", and any other name returns HTTP 400.

Run:  python toolsearch.py "How many loyalty points does Priya have?"
"""

import sys

from common import SMART_MODEL, client

CATALOG = {
    "get_flavor_of_the_day": "Return today's featured cupcake flavor",
    "check_stock": "Check how many cupcakes of a flavor are in stock",
    "place_order": "Place a cupcake order for a customer",
    "cancel_order": "Cancel an existing order by order id",
    "get_loyalty_points": "Look up a customer's loyalty points balance by name",
    "redeem_loyalty_reward": "Redeem loyalty points for a free cupcake",
    "get_store_hours": "Return opening hours for a given day",
    "get_allergen_info": "List allergens for a flavor",
    "get_pricing": "Return the price of a flavor or bundle",
    "schedule_pickup": "Book a pickup time slot for an order",
    "get_order_status": "Check whether an order is ready",
    "list_seasonal_specials": "List the current seasonal specials",
}

tools = [{"type": "tool_search_tool_bm25_20251119", "name": "tool_search_tool_bm25"}] + [
    {
        "name": name,
        "description": desc,
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}},
        "defer_loading": True,      # not in context until tool search finds it
    }
    for name, desc in CATALOG.items()
]

question = sys.argv[1] if len(sys.argv) > 1 else "How many loyalty points does Priya have?"
r = client().messages.create(model=SMART_MODEL, max_tokens=800, tools=tools,
                             messages=[{"role": "user", "content": question}])

print("searched:", [b.input for b in r.content if b.type == "server_tool_use"])
print("found:   ", [ref.tool_name for b in r.content
                    if b.type == "tool_search_tool_result"
                    for ref in getattr(b.content, "tool_references", [])])
print("called:  ", [b.name for b in r.content if b.type == "tool_use"])
