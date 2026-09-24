# Raspberry Pi 5 Setup

Step-by-step instructions for when the Pi arrives. No machine-learning
knowledge needed: the model is already chosen and set in `config.py`.

## What you need

- Raspberry Pi 5 (the 4 GB model is enough)
- A microSD card, 32 GB or bigger
- The official Raspberry Pi 27 W USB-C power supply. Weaker phone chargers
  cause random crashes.
- **An Active Cooler (the small official fan) for the Pi 5.** The detection
  keeps the processor busy all the time. Without a fan, the Pi gets hot and
  slows itself down.
- The camera
- Wi-Fi or a network cable

## 1. Install the operating system

1. On your PC, install **Raspberry Pi Imager** from raspberrypi.com/software.
2. Choose device **Raspberry Pi 5**, then **Raspberry Pi OS (64-bit)**, then
   your microSD card.
3. When it asks about settings, click **Edit settings** and set:
   - hostname: `animal-pi`
   - a username and password (write them down)
   - your Wi-Fi name and password
   - on the **Services** tab: turn on **SSH**
4. Write the card, put it in the Pi, and power it on. The first boot takes a
   few minutes.

## 2. Connect to the Pi

Either plug in a screen and keyboard and open **Terminal**, or connect from
your PC. In PowerShell on the PC, run:

```
ssh YOUR_USERNAME@animal-pi.local
```

All commands below go into that terminal.

## 3. Update the Pi

```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

Connect again after the reboot.

## 4. Download the project

The GitHub repository is private, so log in first:

```bash
sudo apt install -y gh
gh auth login
```

Choose **GitHub.com**, then **HTTPS**, then **Login with a web browser**, and
follow the code it shows. Then run:

```bash
gh repo clone Thananontnc/animal_deterrent
cd animal_deterrent
```

## 5. Install the software

This takes about 10–20 minutes.

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Every time you open a new terminal later, run these two lines first:

```bash
cd ~/animal_deterrent
source .venv/bin/activate
```

## 6. First test with a cat photo

```bash
wget -O cat.jpg http://images.cocodataset.org/val2017/000000039769.jpg
python main.py --source cat.jpg --headless --max-frames 100
```

What you should see:

1. `First run: converting ... to NCNN`. This makes the model several times
   faster on the Pi. It takes a few minutes and happens only once.
2. Then `SPRAYING: cat ...`, then `AIM to pan=...` and `SPRAY for 2s`.

If you see that, the software works on the Pi.

## 7. Test with the camera

- **USB webcam:** plug it in and run `python main.py`. You need a screen
  connected to the Pi to see the video window. Over SSH, use
  `python main.py --headless` instead.
- **Raspberry Pi Camera Module (ribbon cable):** this is not supported yet.
  It needs a small code addition. Ask for it once you know which camera you
  have.

The window shows the speed as **FPS** (frames per second) in the top right.
Anything from 3 FPS upward is fine: a cat stays in the yard for many
seconds, and one confident detection is enough to trigger a spray.

## If it is too slow

Open `config.py` and change the two model lines. Try option A first.

Option A: a bit faster, still accurate (cat found in 90% of test frames,
dog in 65%):

```python
MODEL_PATH = "yolo26n.pt"
IMAGE_SIZE = 960
```

Option B: about twice as fast, but it misses more far-away animals (cat
70%, dog 57%):

```python
MODEL_PATH = "yolo26n.pt"
IMAGE_SIZE = 640
```

The first run after a change converts the model again, which takes a few
minutes.

## Next steps (not built yet)

- Wiring the servos and the water valve. See "Connecting real hardware" in
  `README.md`.
- Starting the program automatically when the Pi turns on.
