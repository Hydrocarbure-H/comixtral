# comixtral
A really simple tool to create formatted commit without typing a word. Powered by AI ;)
# How it works ?
You have the following diff in your git repository:
```
git diff
--
git a/users/serializers.py b/users/serializers.pyindex
f64c80a..e0a715e 100644
---
a/users/serializers.py+++ b/users/serializers.py@@ -20,7 +20,8 @@
class UserResponse(BaseModel):
              'uid': str(self.uid),
              'firstname': self.firstname,
              'lastname': self.lastname,
 -            'email': self.email
 +            'email': self.email,
 +            'password': self.password,
```
You just have the to use the command `comixtral` from your git repository, and the following commit will be added and pushed:
> feat(user): Added 'password' field to UserResponse serializer

# How use it ?
## Installation
- Get a Mixtral Account, with an API KEY
- Git clone this project (or just copy/paste the `comixtral.py` content to a python script)
- Optional: add an alias to your .*rc file:
  - `echo 'alias comixtral="python3 /path/to/your/python/script.py"' >> ~/.zshrc && source ~/.zshrc`
- Create a `.env` file with the following content
  - `echo "MIXTRAL_API_KEY=your_mixtral_api_key" > /path/to/your/python/.env`

## Usage
- Call at any time the `comixtral` command in any git repository

# What about the price ?
If you don't commit every 5 minutes (but this could be a use case actually), you will not reach a huge cost, because there is a limitation (250 tokens) to the size of the input git diff, and the answer only have 10 to 50 tokens.

## My experience
I do about 300 commits a month, and it costs me about 7 cents a month, but save me about 2 hours of writing commits messages.

## More precise estimation
ChatGPT has done some wonderful maths to calculate how much commits we can do with 1EUR :
> Assuming each commit message generation uses around 750 input tokens (the truncated diff) and generates about 50 output tokens, the token usage per call would be approximately 300 tokens.
> 
> Cost per token:
>
> - Input tokens cost: €0.6 / 1,000,000 = €0.0000006 per token
> - Output tokens cost: €1.8 / 1,000,000 = €0.0000018 per token
> 
> Total cost per commit:
> 
> - Input tokens for one commit: 250 tokens × €0.0000006 = €0.00015
> - Output tokens for one commit: 50 tokens × €0.0000018 = €0.00009
> Total cost per commit: €0.00015 + €0.00009 = €0.00024
> 
> Number of commits for €1/month:
> 
> €1 / €0.00024 per commit ≈ **4166 commits**