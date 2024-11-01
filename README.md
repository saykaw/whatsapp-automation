# Project Workflow 

1. Scheduling Script:
A scheduling script sends messages to users at specified times.

2. User Response Handling:
Upon receiving the scheduled message, it is up to the user to respond. User replies are processed via a webhook.

3. Response Generation:
The user's reply is forwarded to the Retrieval-Augmented Generation (RAG) system via the webhook, which generates an appropriate response.

4. Database Storage:
All conversations, including user messages and generated responses, are stored in a database for future reference and analysis.
