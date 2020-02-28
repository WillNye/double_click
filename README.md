# Double Click
> Click + API session management, simple async http requests, Markdown generation, user auth, http response to MVC (plus file caching), and some nice helper functions sprinkled in

### Why use Double Click?
Double Click removes the boiler plate of API centric CLIs with features like:
* User permissions - Hide command if user doesn't have access
* HTTP Session management - refresh auth during long running async operations
* HTTP Sessions tied to a user - Allows for things like `all_roles = {**google_session.user.access, **duo_session.user.access`
* Use HTTP response for click.Choices instead of hard coded values that may not be viable e.g. users
* Normalizing a requests.Response object to a human readable value
* Catching exceptions during async http requests and normalizing to a human readable value
* Displaying complex structures like a bullet list, table, or code snippets in the terminal.
* Local file caching for large API responses with custom TTL
