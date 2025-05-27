From ispider:

```
source venv_dev/bin/activate
python -m build
twine check dist/*
twine upload dist/*0.2.0*
```