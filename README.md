# comixtral
A really simple tool to create formatted commit without typing a word. Powered by AI ;)
### Summary
1. [How it works ?](#how-it-works-)
2. [How use it ?](#how-use-it-)
   - [Installation](#installation)
   - [Usage](#usage)
3. [What about the price ?](#what-about-the-price-)
4. [My experience](#my-experience)
5. [More precise estimation](#more-precise-estimation)
6. [Future Features](#future-features)
   - [pr-summary](#comixtral-pr-summary)
   - [amend](#comixtral-amend)
   - [update](#comixtral-update)
   - [prepare-pr](#comixtral-prepare-pr)
   - [release-note](#comixtral-release-note)

# Screenshots
#### Accurate generated message
<img width="923" alt="image" src="https://github.com/user-attachments/assets/f6c75991-a767-4886-8d34-1d4e24484d50" />

#### Not good enough generated message
(Yep, with small changes, comixtral will not be very original in its new answers...!)
<img width="923" alt="image" src="https://github.com/user-attachments/assets/5e44dd9d-2a3c-4535-9d40-28ff841719e1" />

#### Custom message wanted
<img width="923" alt="image" src="https://github.com/user-attachments/assets/367b23e0-f86b-468b-aaea-34bcb6879f80" />

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

<img width="797" alt="image" src="https://github.com/Hydrocarbure-H/comixtral/assets/97756028/028e5323-00c5-49d7-ab9d-2543be7ed095">


# How use it ?
## Installation
- Get a Mixtral Account, with an API KEY
- Git clone this project (or just copy/paste the `comixtral.py` content to a python script)
- `pip3 install requests python-dotenv --break-system-packages` (it's not a big deal for theses packages but you can also use a virtual env if you don't use it everyday).
- Optional: add an alias to your .*rc file:
  - `echo 'alias comixtral="python3 /path/to/your/python/script.py"' >> ~/.zshrc && source ~/.zshrc`
- Create a `.env` file with the following content
  - `echo "MIXTRAL_API_KEY=your_mixtral_api_key" > /path/to/your/python/.env`

## Usage
- Call at any time the `comixtral` command in any git repository

## Gitixtral Tool
`gitixtral` is a tool designed to automate the creation of pull requests using the GitHub CLI (`gh`). It generates a pull request title and description using Mistral AI based on the changes made in the current branch.

### How to Use Gitixtral
- Ensure the GitHub CLI (`gh`) is installed on your system.
- Run the following command to create a pull request from the current branch into the specified base branch:
  ```bash
  gitixtral <base-branch>
  ```
  Replace `<base-branch>` with the name of the branch you want to merge into.
- The tool will generate a pull request title and description, and prompt you for confirmation before creating the pull request.
<img width="806" alt="image" src="https://github.com/user-attachments/assets/25e1280c-774d-482e-aaef-a8da655f0ec0" />

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

# Future Features
**Résumé des fonctionnalités et commandes**


comixtral pr-summary
- Description : Génère un résumé des commits de la branche actuelle, prêt à être utilisé dans une Pull Request sur GitHub.
- Exemple :
```bash
comixtral pr-summary
```
Output :
```plaintext
# Résumé des modifications
- feat(auth): implement user login flow
- fix(auth): resolve null pointer exception on login
```

comixtral amend
- Description : Combine intelligemment les modifications actuelles avec le dernier commit. Utilise git commit --amend pour regrouper les changements ou corriger le message précédent.
- Exemple :
```bash
comixtral amend
```
Si un fichier oublié est ajouté, le commit est mis à jour sans créer un nouveau commit.

comixtral update
- Description : Automatisation de git checkout dev && git pull, suivie d'un rebase de la branche actuelle sur dev. Cela garantit que ton travail est toujours basé sur les derniers changements.
- Exemple :
```bash
comixtral update
```

comixtral prepare-pr
- Description : Prépare un script qui inclut la création d'une branche, un push, et le lancement de la commande de création d'une PR GitHub (avec gh ou équivalent).
- Exemple :
```bash
comixtral prepare-pr
```

comixtral release-note
- Description : Génère une note de version pour une release basée sur tous les commits depuis le dernier tag Git. Les commits sont regroupés par type (feat, fix, etc.) et formatés pour une publication.
- Exemple :
```bash
comixtral release-note
```
Output :
```plaintext
## [v1.2.0] - 2024-12-19

### Features
- feat(auth): implement user login flow

### Fixes
- fix(auth): resolve null pointer exception on login
```

---
