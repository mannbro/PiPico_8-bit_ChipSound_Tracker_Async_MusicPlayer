import time
from PWMTracker import PWMTracker

pattern = """
----- ----- ----- ----- D--16
----- ----- ----- ----- -----
----- ----- ----- ----- C--16
----- ----- ----- ----- -----
----- ----- ----- ----- D--16
----- ----- ----- ----- -----
----- ----- ----- ----- C--16
----- ----- ----- ----- -----
----- ----- ----- ----- D--16
----- ----- ----- ----- -----
----- ----- ----- ----- C--16
----- ----- ----- ----- -----
----- ----- ----- ----- D--16
----- ----- ----- ----- -----
----- ----- ----- ----- C--16
----- ----- ----- ----- -----
D-401 F#401 A-401 D-416 D--16
----- ----- ----- F#416 -----
----- ----- ----- A-416 C--16
----- ----- ----- F#416 -----
----- ----- ----- D-416 D--16
----- ----- ----- F#416 -----
----- ----- ----- A-416 C--16
----- ----- ----- F#416 -----
----- ----- ----- D-416 D--16
----- ----- ----- F#416 -----
----- ----- ----- A-416 C--16
----- ----- ----- F#416 -----
----- ----- ----- D-416 D--16
----- ----- ----- F#416 -----
----- ----- ----- A-416 C--16
----- ----- ----- F#416 -----
A-401 C#401 E-401 A-416 D--16
----- ----- ----- C#416 -----
----- ----- ----- E-416 C--16
----- ----- ----- C#416 -----
----- ----- ----- A-416 D--16
----- ----- ----- C#416 -----
----- ----- ----- E-416 C--16
----- ----- ----- C#416 -----
----- ----- ----- A-416 D--16
----- ----- ----- C#416 -----
----- ----- ----- E-416 C--16
----- ----- ----- C#416 -----
----- ----- ----- A-416 D--16
----- ----- ----- C#416 -----
----- ----- ----- E-416 C--16
----- ----- ----- C#416 -----
B-401 D-401 F#401 B-416 D--16
----- ----- ----- D-416 -----
----- ----- ----- F#416 C--16
----- ----- ----- D-416 -----
----- ----- ----- B-416 D--16
----- ----- ----- D-416 -----
----- ----- ----- F#416 C--16
----- ----- ----- D-416 -----
----- ----- ----- B-416 D--16
----- ----- ----- D-416 -----
----- ----- ----- F#416 C--16
----- ----- ----- D-416 -----
----- ----- ----- B-416 D--16
----- ----- ----- D-416 -----
----- ----- ----- F#416 C--16
----- ----- ----- D-416 -----
F#401 A-401 C#401 F#416 D--16
----- ----- ----- A-416 -----
----- ----- ----- C#416 C--16
----- ----- ----- A-416 -----
----- ----- ----- F#416 D--16
----- ----- ----- A-416 -----
----- ----- ----- C#416 C--16
----- ----- ----- A-416 -----
----- ----- ----- F#416 D--16
----- ----- ----- A-416 -----
----- ----- ----- C#416 C--16
----- ----- ----- A-416 -----
----- ----- ----- F#416 D--16
----- ----- ----- A-416 -----
----- ----- ----- C#416 C--16
----- ----- ----- A-416 -----
G-401 B-401 D-401 G-416 D--16
----- ----- ----- B-416 -----
----- ----- ----- D-416 C--16
----- ----- ----- B-416 -----
----- ----- ----- G-416 D--16
----- ----- ----- B-416 -----
----- ----- ----- D-416 C--16
----- ----- ----- B-416 -----
----- ----- ----- G-416 D--16
----- ----- ----- B-416 -----
----- ----- ----- D-416 C--16
----- ----- ----- B-416 -----
----- ----- ----- G-416 D--16
----- ----- ----- B-416 -----
----- ----- ----- D-416 C--16
----- ----- ----- B-416 -----
D-401 F#401 A-401 D-416 D--16
----- ----- ----- F#416 -----
----- ----- ----- A-416 C--16
----- ----- ----- F#416 -----
----- ----- ----- D-416 D--16
----- ----- ----- F#416 -----
----- ----- ----- A-416 C--16
----- ----- ----- F#416 -----
----- ----- ----- D-416 D--16
----- ----- ----- F#416 -----
----- ----- ----- A-416 C--16
----- ----- ----- F#416 -----
----- ----- ----- D-416 D--16
----- ----- ----- F#416 -----
----- ----- ----- A-416 C--16
----- ----- ----- F#416 -----
G-401 B-401 D-401 G-416 D--16
----- ----- ----- B-416 -----
----- ----- ----- D-416 C--16
----- ----- ----- B-416 -----
----- ----- ----- G-416 D--16
----- ----- ----- B-416 -----
----- ----- ----- D-416 C--16
----- ----- ----- B-416 -----
----- ----- ----- G-416 D--16
----- ----- ----- B-416 -----
----- ----- ----- D-416 C--16
----- ----- ----- B-416 -----
----- ----- ----- G-416 D--16
----- ----- ----- B-416 -----
----- ----- ----- D-416 C--16
----- ----- ----- B-416 -----
A-401 C#401 E-401 A-416 D--16
----- ----- ----- C#416 -----
----- ----- ----- E-416 C--16
----- ----- ----- C#416 -----
----- ----- ----- A-416 D--16
----- ----- ----- C#416 -----
----- ----- ----- E-416 C--16
----- ----- ----- C#416 -----
----- ----- ----- A-416 D--16
----- ----- ----- C#416 -----
----- ----- ----- E-416 C--16
----- ----- ----- C#416 -----
----- ----- ----- A-416 D--16
----- ----- ----- C#416 -----
----- ----- ----- E-416 C--16
----- ----- ----- C#416 -----
"""

# Create a PWMTracker instance with default melodic pins (12,13,14,15), drum pin 11, and BPM of 60
tracker = PWMTracker(bpm=60)

#Play the pattern asynchronously on core two in a continuous loop
tracker.play_pattern(pattern, async_play=True, loop=True)

#Ok, we don't want to go crazy, so set a timer for 5 minutes
time.sleep(300)

#Stop the tracker
tracker.stop()
print("Asynchronous playback stopped.")
