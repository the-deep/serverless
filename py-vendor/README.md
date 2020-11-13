# Deep serverless

Deep serverless sharable modules.

## Deploy to pypi

```bash
# Create package
python3 setup.py sdist

# Push to pypi (for test use twine -r testpypi)
twine upload dist/*

# Clean build files
rm -rf deep_serverless.egg-info/ dist
```
