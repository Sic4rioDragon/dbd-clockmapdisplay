# dbd-clockmapdisplay

Small Dead by Daylight map OCR overlay for OBS / browser overlay use.

It reads the map name from the game with Tesseract OCR and then shows the matching map image in the overlay.

This is inspired by the private map OCR/callout project from https://github.com/snoggles and the bits of the setup he shared with me.

## current state

Right now the automatic OCR while loading in is not working properly yet.

What **does** work well right now is pressing **F8** while the in-game **tab / match details** screen is open. That already works fine on a lot of maps.

You can change the OCR areas and other settings in:

```text
bot/settings.json
````

## what you need

Install / have these first:

* Python 3
* Tesseract OCR
* ImageMagick
* OBS Studio

You also need the Python packages used by the bot.

## setup

1. Install Python 3
2. Install Tesseract OCR
   Default path used right now:
   `C:\Program Files\Tesseract-OCR\tesseract.exe`
3. Install ImageMagick
4. Run:

```bat
setup_python_deps.bat
```

5. Put your raw map images into:

```text
originals
```

6. Run:

```bat
convert_maps.bat
```

That converts the map images into the format the overlay uses.

## how to run it

Start the bot with:

```bat
run_bot.bat
```

The local overlay should then be available at:

```text
http://127.0.0.1:8765/
```

Add that as a **Browser Source** in OBS if you want to use it there.

## how to use it right now

At the moment the best way to use it is:

1. Load into a match
2. Open the in-game **tab / match details** screen
3. Press **F8**
4. The bot reads the map name and updates the overlay

If needed, you can also use the **Check map** button on the overlay page.

## notes

* Automatic loading-screen OCR still needs work
* F8 + tab/match details already works pretty well on a lot of maps
* Some OCR behavior depends on your resolution / UI scale / game layout
* If your OCR area is off, adjust it in `bot/settings.json`

## planned

* improve automatic loading-screen detection
* improve map OCR on more edge cases
* keep cleaning up the overlay and matching
