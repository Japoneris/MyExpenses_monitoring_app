Code in python.
Use the virtual env: `source venv/bin/activate`
If missing dependencies, install with `pip3` and store it in `requirements.txt`
- Raw data are stored in `data/`
- Code is stored in `src/`

# Translation
Code is translated in english and french. Each time you add "visual text", you should translate it in all supported languages. 
This does not apply to logs.
See `src/i18n.py` and `src/translations/`

# Streamlit remarks

## Page Apps

The streamlit app should be structured with pages.
Only the root page is run by the user, and called `src/app.py`.
Relative pages are stored in `src/pages/`

## Common mistakes

For `use_container_width=True`, use `width='stretch'`. For `use_container_width=False`, use `width='content'`.