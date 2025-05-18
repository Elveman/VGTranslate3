# VGTranslate3

Lightweight server for doing OCR and machine translation on game screen captures.  Suitable as an endpoint for real time usage, and can act as an open-source alternative to the ztranslate client.  Uses python 3.9.  Licensed under GNU GPLv3.

# Installation

1. Download this repo and extract it.  If you have git you can do: `git clone https://github.com/Elveman/VGTranslate3.git` instead.
2. Copy any of JSONs in `config_example` folder to `config.json` (in the `src/vgtranslate3` folder) and modify the configuration to point to the OCR/MT apis you want to use (see the Examples section below).
3. Install python (v3.9 or higher) to your system.
4. Run `python -m venv .venv` to create a new Python environment then `source .venv/bin/activate` to switch to it.
5. Run `python -m pip install -r requirements.txt` in the base folder to install the required packages (in a virtualenv).
6. Run `python -m src.vgtranslate3.serve` to launch the server.


# Example configurations for config.json:

You can use either use Google API keys yourself to run vgtranslate3, or use an account with the ztranslate.net service.  The ZTranslate service in this case basically acts like a standalone vgtranslate3 server that's setup with it's own Google API keys.  The main purpose being that you can try out vgtranslate3 without having to sign up to Google Cloud first, and getting some savings with a volume discount on the Google Cloud api calls.  To get an API key for ZTranslate, go to https://ztranslate.net , sign up, and go to the Settings page.  The ZTranslate API key will be at the bottom.

As of writing, ztranslate.net allows 10,000 calls per month (for free), while if you sign up for Google Cloud, you get $300 worth of API credits.  Each vgtranslate3 call costs about 0.2-0.3 cents, so it makes sense to use the Google API keys directly instead of pooling than with ZTranslate, at least at first.

See: https://cloud.google.com/billing/docs/how-to/manage-billing-account about how to create a Google Cloud account and https://cloud.google.com/docs/authentication/api-keys about creating Google Cloud API keys

If using Google Cloud keys, be sure to set the API key to not have restricted APIs at all, or at least include the Cloud Vision API, Cloud Translation API, and Cloud Text-to-Speech API in the list of allowed APIs. 

### Using ztranslate.net
```
config_example/config_ztranslate.json
```

### Using Google OCR and translation
```
config_example/config_google.json
```

### Using tesseract locally, and then Google translate (experimental):
```
config_example/config_tess_google.json
```

Please note that by default the server address is 0.0.0.0, making it accessible to anyone using the same local network. To use the server with the local RetroArch build, change the address to 127.0.0.1 or localhost.

# Docker
To build:
```
docker build -t vgtranslate3 .
```
To run with the default port (4404):
```
docker run --rm -it -p 4404:4404 docker.io/library/vgtranslate3
```
To run with custom port:
```
docker run --rm -it -e VGTRANSLATE3_PORT=5000 -p 5000:5000 docker.io/library/vgtranslate3
```
Please note that the Docker build requires `config.json` to be placed in the `src/vgtranslate3` folder.

# Note

This is, mostly, a PoC now and a pet project made for personal benefits (like playing JP-only Atlus titles with comfort) since there's tons of progress in AI image recognition and text translation and the original project hasn't been updated for quite a while even though there's a lot of potential here. Please note that while I'm a programmer, Python is not my field of expertise. I'm a C/C++ programmer with some Python knowledge and some common sense, so AI coding helpers are used (within reason).

# Roadmap

- [x] Python 3 port
- [x] Proper config files (pyproject.toml, requirements.txt)
- [ ] Proper Tesseract support
- [x] Docker support
- [ ] Proper TTS testing
- [ ] Yandex Translate support
- [ ] Other gRPC services support
- [ ] OpenAI API support
- [ ] Full on-device translation support
- [ ] Refactoring

# Credits
[This awesome person](https://gitlab.com/spherebeaker/vgtranslate) did most of the work. I'm just building on top of it.

