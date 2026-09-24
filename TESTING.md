# Test Plan: Phone Camera

A checklist for testing the full pipeline with a live camera. It uses a
phone as the camera, because the PC has no webcam. Tick each box as you go
and write down anything that does not match the expected result.

## What was already tested

These passed on the PC with photos and video files, not a live camera:

- [x] Decision rule unit tests (8 of 8 pass)
- [x] Cat photo: SPRAY, then IDLE for the 5 s cooldown, then SPRAY again
- [x] Photo of people: PAUSED
- [x] Photo with both cats and people: PAUSED
- [x] Video of a person, then only cats: first spray about 20 s after the person leaves
- [x] Video window opens, draws boxes and state, and closes cleanly
- [x] MJPEG network stream as `--source` (the same format phone apps send)

Not tested yet: a real live camera, real animals outdoors, the Raspberry Pi 5,
and the real servos and valve.

## 1. Setup (about 10 minutes)

On the PC:

```powershell
git clone https://github.com/Thananontnc/animal_deterrent.git
cd animal_deterrent
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m unittest test_decision
```

- [ ] `pip install` finishes with no errors
- [ ] The unit tests print `OK`

If you still have the folder from before, skip the clone and the install.
Run `.venv\Scripts\Activate.ps1` in the project folder instead.

## 2. Connect the phone camera

1. Connect the phone and the PC to the same Wi-Fi network.
2. Install **IP Webcam** (Android) or **DroidCam** (Android or iPhone).
3. Start the stream in the app and note the IP address it shows.
4. Check the stream in a web browser on the PC first:
   - IP Webcam: `http://PHONE_IP:8080/video`
   - DroidCam: `http://PHONE_IP:4747/video`
5. Close the browser tab. DroidCam only allows one viewer at a time.
6. Start the system:

   ```powershell
   python main.py --source http://PHONE_IP:8080/video
   ```

- [ ] The browser shows the phone's camera
- [ ] The "Animal Deterrent" window opens and shows live video
- [ ] The window shows a state (`IDLE`, `PAUSED` or `SPRAYING`) and an FPS number

Write down the FPS: ______

## 3. Person tests (safety)

The system must never spray while a person is in view. These are the most
important tests.

| # | Do this | Expected result | Pass? |
|---|---------|-----------------|-------|
| 3.1 | Point the phone at an empty room | `IDLE`, "nothing detected" | [ ] |
| 3.2 | Stand in full view | `PAUSED`, "person in frame", green box on you | [ ] |
| 3.3 | Show only your hand or arm | `PAUSED` (note if it does not) | [ ] |
| 3.4 | Stand far away, at the other side of the room | `PAUSED` | [ ] |
| 3.5 | Stand partly behind a door or furniture | `PAUSED` | [ ] |
| 3.6 | Walk out of view | `PAUSED`, "person left, resume in 20s" counting down | [ ] |
| 3.7 | Wait 20 s with nobody in view | Changes to `IDLE` | [ ] |
| 3.8 | Walk back in during the countdown | Countdown restarts from 20 s | [ ] |

Note any test where the green person box flickers on and off. Flicker means
the person confidence is close to `PERSON_CONFIDENCE_THRESHOLD` (0.30).

## 4. Animal tests

Keep yourself out of view for these. If any part of you is visible, the
system pauses, which is correct.

| # | Do this | Expected result | Pass? |
|---|---------|-----------------|-------|
| 4.1 | Show a cat photo on another screen (a laptop, a monitor, or a second phone) | `SPRAYING`, red box, red cross on the cat. Terminal prints `AIM ...` and `SPRAY for 2s` | [ ] |
| 4.2 | Keep the cat in view | `IDLE` with "cooldown" for about 3 s, then `SPRAYING` again, every 5 s | [ ] |
| 4.3 | Move the cat to the left side of the video window, then the right | `pan` in the terminal is negative on the left and positive on the right | [ ] |
| 4.4 | Move the cat to the top of the video window, then the bottom | `tilt` is positive at the top and negative at the bottom | [ ] |
| 4.5 | Show a dog photo | `SPRAYING` | [ ] |
| 4.6 | Show a bird photo | `SPRAYING` | [ ] |
| 4.7 | Show the cat photo, then step into view | `PAUSED` at once. Terminal prints `STOP spray` if it was spraying | [ ] |
| 4.8 | Real pet, if you have one | `SPRAYING` | [ ] |

Photos on a screen are harder for the model than real animals: glare, low
resolution and screen borders all get in the way. If a photo is not detected,
try a bigger, brighter photo before you decide the model failed.

## 5. Yard test (optional, but the most useful)

Take the phone outside and point it at the yard, where the real camera will
go.

- [ ] Nobody in the yard: stays `IDLE` for 5 minutes, with no false sprays
- [ ] You walk across the yard: `PAUSED` the whole time
- [ ] You stand at the far end of the yard: still `PAUSED`
- [ ] Any animal that visits: detected? At what confidence? ______

Record a few minutes of yard video on the phone at different times of day
(morning, noon, dusk). You can replay a recording later with
`python main.py --source yard.mp4`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Could not open video source` | Check the stream URL in a browser first. Check that both devices are on the same Wi-Fi. Close other viewers (DroidCam). |
| The browser works but Python does not | Allow Python through Windows Firewall, or try the other app. |
| Video is very laggy | Lower the resolution in the phone app (640x480 is enough). |
| A person is sometimes missed | Lower `PERSON_CONFIDENCE_THRESHOLD` in `config.py`. |
| Things that are not animals trigger a spray | Raise `CONFIDENCE_THRESHOLD` in `config.py`. |
| Waiting 20 s between tests is too slow | Lower `PERSON_DEBOUNCE_SECONDS` while testing. Set it back afterwards. |

## Results to bring back

- FPS: ______
- Failed tests (numbers): ______
- Lowest person confidence seen while you were clearly in view: ______
- Any false spray (something that is not an animal): ______
- Animal confidence scores seen: ______
