# Sample Queries

Test your Multimodal Product Search Agent with these queries.

## Text-Based Semantic Search
These queries require the agent to generate text embeddings and perform vector search:

1. **Descriptive Search**
   - "Find me a comfortable everyday bag"
   - "Show me elegant evening accessories"
   - "I need something warm for winter"

2. **Style-Based Search**
   - "Bohemian summer outfit pieces"
   - "Minimalist professional accessories"
   - "Edgy street style items"

3. **Occasion-Based Search**
   - "What should I wear to a cocktail party?"
   - "Beach vacation essentials"
   - "Office-appropriate footwear"

## Image-Based Search
These queries involve the user providing a product image:

1. **Visual Similarity**
   - "Find products that look like this" (+ image)
   - "Show me similar items" (+ image of a leather bag)
   - "What do you have that matches this style?" (+ image)

> **Tip**: In the Foundry playground, you can paste base64-encoded images or image URLs.

## Hybrid Search (Text + Image)
These combine an image with text modifications:

1. **Color Variation**
   - "Shoes like this but in black" (+ image of red sneakers)
   - "Similar bag in brown" (+ image of a black bag)

2. **Style Modification**
   - "Something like this but more casual" (+ image of a formal dress)
   - "Similar to this but for outdoor use" (+ image of a leather bag)

## Direct Filter Queries
These query MongoDB directly by field values:

1. **By Category**
   - "Show me all shoes"
   - "List available bags"
   - "What dresses do you have?"

2. **By Brand**
   - "Show me Heritage brand products"
   - "What does LuxeNoir offer?"
   - "ActiveGear products"

3. **By Price**
   - "Products under $50"
   - "Luxury items over $150"
   - "What's your cheapest bag?"

4. **By Color/Material**
   - "Black leather items"
   - "All products in red"
   - "What do you have in wool?"

5. **Combined Filters**
   - "Red dresses under $70"
   - "Leather shoes between $100 and $200"
   - "Black bags from UrbanCraft"

## Aggregation Queries
These use MongoDB aggregation pipelines:

1. **Statistics**
   - "What's the average price by category?"
   - "How many products per brand?"
   - "Price range for shoes"

2. **Rankings**
   - "Most expensive products"
   - "Cheapest items in each category"
   - "Which category has the most products?"

3. **Grouped Analysis**
   - "Show me all available colors for bags"
   - "What materials are used for shoes?"
   - "Brand breakdown by category"

## Complex Multi-Step Queries
These may require multiple tool calls:

1. "Find leather accessories similar in style to this bag" (+ image) + filter by material
2. "What's the cheapest product visually similar to a red handbag?"
3. "Show me outerwear options that would go well with black leather boots"

## Expected Behavior

| Query Type | Tools Used | Input |
|------------|------------|-------|
| Semantic text | EmbeddingGenerator → MongoDB | text only |
| Visual similarity | EmbeddingGenerator → MongoDB | image only |
| Hybrid | EmbeddingGenerator → MongoDB | text + image |
| Direct filters | MongoDB only | field values |
| Aggregations | MongoDB only | pipeline |
| Hybrid + filter | EmbeddingGenerator → MongoDB + $match | text/image + fields |
