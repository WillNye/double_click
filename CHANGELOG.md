# Change Log

---

# 0.2.11 (2020/04/08)

### Bug Fixes
* Properly accounting for key miss in Model.objects_get 
### Features
* None

---

# 0.2.10 (2020/04/02)

### Bug Fixes
* Set a default terminal size if running in supervisor
### Features
* None

---

# 0.2.9 (2020/03/11)

### Bug Fixes
* ensure_latest_package now supports dedicated kwarg for passing pip args to update_package
### Features
* None

---

# 0.2.8 (2020/03/05)

### Bug Fixes
* Catching import inconsistency for get_python_lib
### Features
* Removed Click dependency to expand potential use-cases
* Improved Windows support

---

# 0.2.7 (2020/03/04)

### Bug Fixes
* Cleaned up doc typos
### Features
* None

---

# 0.2.6 (2020/03/03)

### Bug Fixes
* Fixed setattr on User.get if default is provided
### Features
* Added testing

---

# 0.2.5 (2020/03/03)

### Bug Fixes
* Bug fixes for User.has_access and User.hide
* UserSession.refresh_auth fixed to use user.authenticate() response

### Features
* Added a ModelAuth class
* Improved documentation
* Refactor of Model and its attribute naming

---

# 0.1.0 (2020/02/28)

### Bug Fixes
* None

### Features
* Initial Release
