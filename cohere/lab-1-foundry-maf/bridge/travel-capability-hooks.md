# Bridge from Lab 1 to Lab 2: Travel Capability Hooks

Use the travel-concierge story as your guide. 
- Lab 1 builds the main car. 
- Lab 2 shows special parts you can bolt on when the app needs better search, clearer relationships, or smarter sorting.


Use these prompts when learners ask, "if only my concierge could..." 

- Each hook maps the Lab 1 travel concierge to a Lab 2 Cohere capability.
- An **embedding** is a number fingerprint for text or images. It helps the concierge find trips that mean the same thing, even when the words are different. 
- **Rerank** means taking a first shortlist and sorting it again using a more detailed user need. 
- A **business graph** is a map of relationships, such as which traveler uses which route, supplier, or policy rule.

<br/>

| If only my concierge could ... | Cohere capability |
| --- | --- |
| find trips that _feel like_ my last successful customer visit | Lab 2a embed - use Cohere Embed to search semantically similar itineraries |
| show how policy, suppliers, routes, and employees relate | Lab 2b business graphs - model travel entities and relationships |
| re-rank hotels after I say I hate red-eyes and need a gym | Lab 2c rerank - reorder a shortlist using updated preferences |
| re-rank flight choices after my manager says refundable fares matter most | Lab 2d rerank - combine policy, price, and flexibility signals |
| re-rank an entire itinerary bundle, not just one hotel or flight | Lab 2e rerank - compare multi-item travel packages for best fit |
