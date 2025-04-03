import time
import math
import _thread
from machine import Pin, PWM
import rp2

#There is probably a smarter way to do this, but what I'm doing here
#is generating a random-like pattern that will sound similar to white
#noise, so that we can generate NES style "drum" beats by alternating
#setting the pin to low and high with a "random" number of cycles as
#delay in between. A pull request with a smarter way of doing it is
#appreciated :-)
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def test():
    wrap_target()
    set(pins, 1)   [31]
    set(pins, 0)   [20]
    set(pins, 1)   [0]
    set(pins, 0)   [5]
    set(pins, 1)   [10]
    set(pins, 0)   [28]
    set(pins, 1)   [7]
    set(pins, 0)   [15]
    set(pins, 1)   [25]
    set(pins, 0)   [21]
    set(pins, 1)   [18]
    set(pins, 0)   [2]
    set(pins, 1)   [5]
    set(pins, 0)   [26]
    set(pins, 1)   [7]
    set(pins, 0)   [23]
    set(pins, 1)   [29]
    set(pins, 0)   [13]
    set(pins, 1)   [30]
    set(pins, 0)   [4]
    set(pins, 1)   [8]
    set(pins, 0)   [24]
    set(pins, 1)   [1]
    set(pins, 0)   [30]
    set(pins, 1)   [5]
    set(pins, 0)   [2]
    set(pins, 1)   [27]
    set(pins, 0)   [25]
    set(pins, 1)   [0]
    set(pins, 0)   [19]
    set(pins, 1)   [26]
    set(pins, 0)   [11]
    wrap()


class PWMTracker:
    # Mapping note lengths to tick counts
    NOTE_LENGTH_TICKS = {
        '01': 16,  # whole note
        '02': 8,   # half note
        '04': 4,   # quarter note
        '08': 2,   # eighth note
        '16': 1    # sixteenth note
    }

    # Mapping from note letter to semitone offset within an octave (using MIDI note formula)
    NOTE_BASE = {
        'C': 0,
        'D': 2,
        'E': 4,
        'F': 5,
        'G': 7,
        'A': 9,
        'B': 11
    }

    def __init__(self, pin1=12, pin2=13, pin3=14, pin4=15, pin_drum=11, bpm=120):
        """
        Initialize PWMTracker with four melodic pins, a drum pin, and a BPM value.
        """
        self.bpm = bpm
        self.tick_duration = (60 / bpm) / 4  # one 16th note duration
        self.pins = [pin1, pin2, pin3, pin4]
        self.pwms = []
        # Initialize PWM channels for each melodic pin with a 50% duty cycle (16-bit resolution)
        for p in self.pins:
            pwm = PWM(Pin(p))
            pwm.freq(440)
            pwm.duty_u16(0)
            self.pwms.append(pwm)
            
        # State for melodic channels (indices 0-3)
        self.channel_states = [{'active': False, 'ticks': 0, 'duration': 0} for _ in range(4)]
        
        # Initialize drum and cymbal StateMachines (using rp2)
        self.drum = rp2.StateMachine(0, test, freq=2500, set_base=Pin(pin_drum))
        self.cymbal = rp2.StateMachine(1, test, freq=20000, set_base=Pin(pin_drum))
        # States for drum and cymbal channels
        self.drum_state = {'active': False, 'ticks': 0, 'duration': 0}
        self.cymbal_state = {'active': False, 'ticks': 0, 'duration': 0}
        
        # Control flag for thread execution
        self._running = False

    def note_to_freq(self, note, accidental, octave):
        """
        Convert note details to frequency using standard A4=440Hz reference.
        """
        if note.upper() not in self.NOTE_BASE:
            return None
        
        semitone = self.NOTE_BASE[note.upper()]
        if accidental == '#':
            semitone += 1
        elif accidental == 'b':
            semitone -= 1

        try:
            octave = int(octave)
        except ValueError:
            return None

        midi_number = (octave + 1) * 12 + semitone
        freq = 440 * (2 ** ((midi_number - 69) / 12))
        return int(freq)

    def _parse_column(self, col_str, row_idx, channel_idx):
        """
        Parse a 5-character column string for melodic channels.
        """
        if len(col_str) != 5:
            print("Warning: Row {} Column {} is not 5 characters. Treated as '-----'".format(row_idx+1, channel_idx+1))
            return None

        if col_str[0] == '-':
            return None

        note = col_str[0]
        accidental = col_str[1]
        octave = col_str[2]
        length_code = col_str[3:5]
        
        if note.upper() not in self.NOTE_BASE:
            print("Warning: Invalid note '{}' in row {} column {}. Treated as '-----'".format(note, row_idx+1, channel_idx+1))
            return None

        if accidental not in ['#', 'b', '-']:
            print("Warning: Invalid accidental '{}' in row {} column {}. Treated as natural.".format(accidental, row_idx+1, channel_idx+1))
            accidental = '-'
            
        if length_code not in self.NOTE_LENGTH_TICKS:
            print("Warning: Invalid note length '{}' in row {} column {}. Treated as empty.".format(length_code, row_idx+1, channel_idx+1))
            return None
        
        ticks = self.NOTE_LENGTH_TICKS[length_code]
        return {'note': note, 'accidental': accidental if accidental != '-' else '', 'octave': octave, 'length_code': length_code, 'ticks': ticks}

    def _parse_drum_column(self, col_str, row_idx):
        """
        Parse a 5-character column string for the drum/cymbal channel.
        The first character must be 'D' (drum) or 'C' (cymbal).
        The 2nd and 3rd characters are ignored.
        The 4th and 5th characters represent note length.
        """
        if len(col_str) != 5:
            print("Warning: Row {} Drum Column is not 5 characters. Treated as '-----'".format(row_idx+1))
            return None

        if col_str[0] == '-':
            return None

        drum_type = col_str[0].upper()
        if drum_type not in ['D', 'C']:
            print("Warning: Invalid drum type '{}' in row {}. Treated as '-----'".format(col_str[0], row_idx+1))
            return None

        length_code = col_str[3:5]
        if length_code not in self.NOTE_LENGTH_TICKS:
            print("Warning: Invalid drum note length '{}' in row {}. Treated as empty.".format(length_code, row_idx+1))
            return None

        ticks = self.NOTE_LENGTH_TICKS[length_code]
        return {'type': drum_type, 'length_code': length_code, 'ticks': ticks}

    def _start_note(self, channel_idx, note_data):
        """
        Start playing a melodic note on the given channel immediately.
        """
        freq = self.note_to_freq(note_data['note'], note_data['accidental'], note_data['octave'])
        if freq is None:
            print("Warning: Could not calculate frequency for note data:", note_data)
            return
        
        self.pwms[channel_idx].freq(freq)
        self.pwms[channel_idx].duty_u16(32768)
        self.channel_states[channel_idx] = {'active': True, 'ticks': 1, 'duration': note_data['ticks']}

    def _stop_note(self, channel_idx):
        """
        Stop playing the melodic note on the given channel.
        """
        self.pwms[channel_idx].duty_u16(0)
        self.channel_states[channel_idx] = {'active': False, 'ticks': 0, 'duration': 0}

    def _start_drum(self, drum_data):
        """
        Start the drum sound.
        """
        self.drum.active(1)
        self.drum_state = {'active': True, 'ticks': 1, 'duration': drum_data['ticks']}

    def _stop_drum(self):
        """
        Stop the drum sound.
        """
        self.drum.active(0)
        self.drum_state = {'active': False, 'ticks': 0, 'duration': 0}

    def _start_cymbal(self, cymbal_data):
        """
        Start the cymbal sound.
        """
        self.cymbal.active(1)
        self.cymbal_state = {'active': True, 'ticks': 1, 'duration': cymbal_data['ticks']}

    def _stop_cymbal(self):
        """
        Stop the cymbal sound.
        """
        self.cymbal.active(0)
        self.cymbal_state = {'active': False, 'ticks': 0, 'duration': 0}

    def _process_tick(self, row_str, row_idx):
        """
        Process a single tick (row) of the pattern.
        Now expects 5 columns: 4 melodic and 1 drum/cymbal.
        """

        cols = row_str.split()
        if len(cols) != 5:
            print("Warning: Row {} does not have exactly 5 columns. Missing columns will be treated as '-----'".format(row_idx+1))
            while len(cols) < 5:
                cols.append("-----")
        
        # Process melodic channels (columns 0-3)
        for ch in range(4):
            col = cols[ch]
            note_data = self._parse_column(col, row_idx, ch)
            state = self.channel_states[ch]
            if note_data:
                self._start_note(ch, note_data)
            else:
                if state['active']:
                    if state['ticks'] >= state['duration']:
                        self._stop_note(ch)
                    else:
                        self.channel_states[ch]['ticks'] += 1

        # Process drum/cymbal channel (column 4)
        drum_data = self._parse_drum_column(cols[4], row_idx)
        if drum_data:
            if drum_data['type'] == 'D':
                self._start_drum(drum_data)
            elif drum_data['type'] == 'C':
                self._start_cymbal(drum_data)
        else:
            # No new drum/cymbal command; check current states.
            if self.drum_state['active']:
                if self.drum_state['ticks'] >= self.drum_state['duration']:
                    self._stop_drum()
                else:
                    self.drum_state['ticks'] += 1
            if self.cymbal_state['active']:
                if self.cymbal_state['ticks'] >= self.cymbal_state['duration']:
                    self._stop_cymbal()
                else:
                    self.cymbal_state['ticks'] += 1

    def _play_pattern_thread(self, pattern, loop):
        """
        Process the pattern row by row in a separate thread.
        If loop is True, after reaching the end of the pattern it will restart.
        """
        self._running = True
        while self._running:
            rows = pattern.splitlines()
            row_count = len(rows)
            row_idx = 0
            while row_idx < row_count and self._running:
                row = rows[row_idx].strip()
                if row == "":
                    row_idx += 1
                    continue
                self._process_tick(row, row_idx)
                time.sleep(self.tick_duration)
                row_idx += 1
            # If loop is False, break out after one full pass through the pattern.
            if not loop:
                break

        # Stop any active sounds at the end of playback.
        for ch in range(4):
            if self.channel_states[ch]['active']:
                self._stop_note(ch)
        if self.drum_state['active']:
            self._stop_drum()
        if self.cymbal_state['active']:
            self._stop_cymbal()
        self._running = False

    def play_pattern(self, pattern, async_play=False, loop=False):
        """
        Play the provided pattern.
        If async_play is True, the pattern is processed on a new thread.
        The loop parameter controls whether the pattern should repeat.
        """
        if async_play:
            _thread.start_new_thread(self._play_pattern_thread, (pattern, loop))
        else:
            self._play_pattern_thread(pattern, loop)


    def stop(self):
        """
        Stop playback immediately.
        """
        self._running = False
        for ch in range(4):
            if self.channel_states[ch]['active']:
                self._stop_note(ch)
        if self.drum_state['active']:
            self._stop_drum()
        if self.cymbal_state['active']:
            self._stop_cymbal()


