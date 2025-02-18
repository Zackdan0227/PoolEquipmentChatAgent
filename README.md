# Pool Equipment Chat Agent 

## Features 

- **Natural Language Understanding**: Process free-form user queries about pool equipment
- **Multi-Intent Detection**: Automatically classify user intentions using both rule-based and AI approaches
- **Product Search**: Utilize multiple search engines (Klevu and Azure Cognitive Search) for robust product discovery
- **Price Checking**: Look up current pricing for specific parts
- **Store Information**: Provide store locations, hours, and contact details
- **Smart Fallbacks**: Gracefully handle failed queries with intelligent retry mechanisms

## Architecture 

### Core Components

1. **Telegram Bot Interface**
   - Handles user interactions
   - Manages message formatting
   - Provides typing indicators for better UX

2. **Agent Manager**
   - Orchestrates the query processing pipeline
   - Implements intent detection
   - Manages API interactions

3. **Search Engines**
   - Primary: Klevu Search
   - Fallback: Azure Cognitive Search
   - Direct part number lookups

### Intent Detection System

The agent uses a two-tier intent detection system:

1. **Direct Pattern Matching**
   - Regex-based part number detection
   - Keyword-based intent classification

2. **GPT-4 Planning**
   - Natural language understanding
   - Context-aware intent classification
   - Parameter extraction

### Supported Intents

- `PRODUCT_SEARCH`: General product queries
- `PRODUCT_PRICE`: Price-specific inquiries
- `PRODUCT_INFO`: Detailed product information
- `STORE_INFO`: Store location and hours

## Technical Stack 

- **Backend Framework**: Python
- **AI/ML**:
  - OpenAI GPT-4
  - LangChain
- **Search Engines**:
  - Azure Cognitive Search
  - Klevu Search
- **Bot Platform**: Telegram Bot API
- **APIs**:
  - Custom Product API
  - Pricing API
  - Store Location API

## Query Processing Pipeline 

1. **Input Processing**
   - User sends query via Telegram
   - Bot initiates typing indicator
   - Query is passed to Agent Manager

2. **Intent Detection**
   - Pattern matching for direct queries
   - GPT-4 analysis for complex queries
   - Intent classification and parameter extraction

3. **Search Execution**
   - Select appropriate API endpoint
   - Execute search with fallback mechanisms
   - Format and validate results

4. **Response Generation**
   - Context-aware response formatting
   - Rich media inclusion (images, links)
   - User-friendly summaries

## Local Development

1. Clone this repository.
2. Install dependencies: `pip install -r requirements.txt` and setup venv
3. Add the following .env:
```
BOT_TOKEN=7863539717:AAE4Lli8ItnVOSA0wk18fL9lSWXjnKG4kcQ
QUERY_API_URL=your_api_base_url
OPENAI_API_KEY=your_openai_api_key
PRICING_TOKEN=your_pricing_api_token
```
4. Run `python -m bot`
5. Open the telegram [chatbot](t.me/PoolingEquipmentbot)


## Future Improvements

1. Right now the chatbot does not have a back and fourth capabality to handle edge case user queries. Add a fail safe agent to detect edge case user input and then ask user to input response again. We can provide user with preprogrammed options in buttons by the intents.
2. This is down in local development with long pooling in HTTP so we are sending requests to the Telegram api and client and awaits for response. This can be improved using deployed backend with a webhook URL to POST data and receive faster response time.
3. I used a GPT to summarize the results from the search engine, this turns out to be slower than just hard coding the format.
4. There could be a ranking system used to better make use of the searching engines, for example, I am using the default page and page items listing from the searched results. Most of the time the searched results are pretty accurate in the first 3-5 results. I was able to get the exact product from the returned json. But I can imagine where user does not have a specefic model in mind, so the chatbot should use the back and fourth capability mentioned in part one to improve the user's query.


