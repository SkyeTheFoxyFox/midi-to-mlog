import mido, colorsys, sys, math
from pymsch import Schematic, Block, Content, ProcessorConfig, ProcessorLink


def GLOBAL_ERROR(message):
	print(f"ERROR:", message)
	sys.exit()

class Arguments:
	def __init__(self, argv):
		self.file = ""
		self.out_file = ""
		self.copy = False
		self.vfx = False
		self.prog_overrides = []
		self.drum_overrides = []
		self.positional = False
		self.positional_pos = ['@thisx', '@thisy']
		self.limit = False
		self.drum_vol_mod = 1
		self.note_vol_mod = 1

		self.args = argv[1:].copy()

		self.__handle_args__()

	def __pop_arg__(self, arg, val):
		try:
			v = self.args.pop(0)
			if(v[0:2] == '--'):
				GLOBAL_ERROR(f"Command '{arg}' expected another value '{val}', instead found '{v}'")
			else:
				return(v)
		except IndexError:
			GLOBAL_ERROR(f"Command '{arg}' expected another value '{val}'")

	def __pop_int__(self, arg, val):
		popped = self.__pop_arg__(arg, val)
		try:
			return int(popped)
		except:
			GLOBAL_ERROR(f"Command '{arg}' at value '{val}' expected int, found '{popped}'")

	def __pop_int_range__(self, arg, val, min_val, max_val):
		popped = self.__pop_arg__(arg, val)
		try:
			if int(popped) in range(min_val, max_val+1):
				return int(popped)
			else:
				GLOBAL_ERROR(f"Command '{arg}' at value '{val}' expected int in range [{min_val}, {max_val}], found '{popped}'")
		except:
			GLOBAL_ERROR(f"Command '{arg}' at value '{val}' expected int in range [{min_val}, {max_val}], found '{popped}'")

	def __pop_float__(self, arg, val):
		popped = self.__pop_arg__(arg, val)
		try:
			return float(popped)
		except:
			GLOBAL_ERROR(f"Command '{arg}' at value '{val}' expected float, found '{popped}'")

	def __pop_bool__(self, arg, val):
		popped = self.__pop_arg__(arg, val)
		if popped in ["false", "False"]:
			return False
		elif popped in ["true", "True"]:
			return True
		else:
			GLOBAL_ERROR(f"Command '{arg}' at value '{val}' expected bool, found '{popped}'")

	def __pop_quoted__(self, arg, val):
		popped = self.__pop_arg__(arg, val)
		if popped[0] == '"' and popped[-1] == '"':
			return popped[1:-1]
		else:
			return popped

	def __handle_args__(self):
		while(self.args != []):
			arg = None
			try:
				arg = self.args.pop(0)
			except:
				pass
			if(arg[0:2] != '--'):
				GLOBAL_ERROR(f"Unknown command '{arg}', try --help")
			arg = arg[2:]
			try:
				if('__' in arg):
					GLOBAL_ERROR(f"Unknown command '{arg}', try --help")
				else:
					getattr(Arguments, arg)(self)
			except AttributeError:
				GLOBAL_ERROR(f"Unknown command '{arg}', try --help")

	def mid(self):
		self.file = self.__pop_quoted__('mid', 'file')

	def out(self):
		self.out_file = self.__pop_quoted__('out', 'file')

	def copy(self):
		self.copy = True

	def drum(self):
		drum_id = self.__pop_int_range__('drum', 'drum', 0, 127) 
		sound = self.__pop_quoted__('drum', 'sound')
		pitch = self.__pop_float__('drum', 'pitch')
		volume = self.__pop_float__('drum', 'volume')
		self.drum_overrides.append({"drum": drum_id, "sound": sound, "pitch": pitch, "volume": volume})

	def prog(self):
		prog = self.__pop_int_range__('prog', 'program', 1, 128) - 1
		sound = self.__pop_quoted__('prog', 'sound')
		note = self.__pop_int_range__('prog', 'note', 0, 127)
		volume = self.__pop_float__('prog', 'volume')
		loop = self.__pop_bool__('prog', 'loop')
		if not loop:
			self.prog_overrides.append({"prog": prog, "sound": sound, "note": note, "volume": volume, "loop": False, "length": 1000})
		else:
			length = self.__pop_float__('prog', 'length')
			self.prog_overrides.append({"prog": prog, "sound": sound, "note": note, "volume": volume, "loop": True, "length": length})

	def vfx(self):
		self.vfx = True

	def pos(self):
		self.positional = True
		target = self.__pop_arg__('pos', 'target')
		if(target == 'self'):
			self.positional_pos = ['@thisx', '@thisy']
		elif(target == 'location'):
			self.positional_pos = [self.__pop_arg__('pos', 'x'), self.__pop_arg__('pos', 'y')]
		else:
			GLOBAL_ERROR(f"Command 'pos' at value 'target' expected either 'self' or 'location', found '{target}'")

	def limit(self):
		self.limit = True

	def drumvol(self):
		self.drum_vol_mod = self.__pop_float__('drumvol', 'volume')

	def notevol(self):
		self.note_vol_mod = self.__pop_float__('notevol', 'volume')

	def help(self):
		print("""
Available commands:

	--mid \033[4mFILE\x1B[0m
		The input midi file path. Mandatory

	--out \x1B[4mFILE\x1B[0m
		Output the schematic as a file.

	--copy
		Write the schematic to your clipboard.

	--vfx
		Show effects over the processor when a note is played.

	--help
		Show this text.

	--pos self
		Makes the sounds come from their respective processors.

	--pos location \x1B[4mX\x1B[0m \x1B[4mY\x1B[0m
		Makes the sounds play at a specific position.

	--drumvol \x1B[4mVOLUME\x1B[0m
		Changes the volume of the drums. 0 is muted, 1 is normal volume.

	--notevol \x1B[4mVOLUME\x1B[0m
		Changes the volume of notes. 0 is muted, 1 is normal volume.

	--drum \x1B[4mDRUM\x1B[0m \x1B[4mSOUND\x1B[0m \x1B[4mPITCH\x1B[0m \x1B[4mVOLUME\x1B[0m
		Changes one of the drum sounds.

		\x1B[4mDRUM\x1B[0m: The drum number.
		\x1B[4mSOUND\x1B[0m: The ingame sound. (E.G. @sfx-pew) 
		\x1B[4mPITCH\x1B[0m: The pitch multiplier.
		\x1B[4mVOLUME\x1B[0m: The volume multiplier.

	--prog \x1B[4mPROGRAM\x1B[0m \x1B[4mSOUND\x1B[0m \x1B[4mNOTE\x1B[0m \x1B[4mVOLUME\x1B[0m \x1B[4mLOOP\x1B[0m [\x1B[4mLENGTH\x1B[0m]
		Changes one of the programs.

		\x1B[4mPROGRAM\x1B[0m: The program number.
		\x1B[4mSOUND\x1B[0m: The ingame sound. (E.G. @sfx-press) 
		\x1B[4mNOTE\x1B[0m: The midi note of the sound.
		\x1B[4mVOLUME\x1B[0m: The volume multiplier.
		\x1B[4mLOOP\x1B[0m: Whether or not this sound should loop.
		\x1B[4mLENGTH\x1B[0m: If loop is true, the length of the sound in ms.
""")
		sys.exit()

def get_programs(prog_overrides, vol_mod):
	programs = []
	for i in range(128):
		programs.append({"sound": "@sfx-press", "note": 60, "volume": 20, "loop": False, "length": 1000})
		#programs.append({"sound": "@sfx-chatMessage", "note": 78, "volume": 2, "loop": False, "length": 1000})
		#programs.append({"sound": "@sfx-back", "note": 69, "volume": 0, "loop": False, "length": 1000})

	programs[29] = {"sound": "@sfx-mineDeploy", "note": 31, "volume": 1, "loop": True, "length": 146}
	programs[30] = {"sound": "@sfx-mineDeploy", "note": 31, "volume": 1, "loop": True, "length": 146}
	programs[31] = {"sound": "@sfx-mineDeploy", "note": 31, "volume": 1, "loop": True, "length": 146}
	programs[32] = {"sound": "@sfx-mineDeploy", "note": 31, "volume": 1, "loop": True, "length": 146}

	for v in prog_overrides:
		programs[v["prog"]] = {"sound": v["sound"], "note": v["note"], "volume": v["volume"], "loop": v["loop"], "length": v["length"]}

	for prog in programs:
		prog["volume"] = prog["volume"] * vol_mod

	return programs

def get_drums(drum_overrides, vol_mod):
	drums = []
	for i in range(128):
		drums.append({"sound": "@sfx-pew", "note": 1, "volume": 0})

	drums[35] = {"sound": "@sfx-place", "note": 0.4, "volume": 0.3}
	drums[36] = {"sound": "@sfx-place", "note": 0.5, "volume": 0.3}
	drums[37] = {"sound": "@sfx-pew", "note": 1, "volume": 0.2}
	drums[38] = {"sound": "@sfx-flame", "note": 1.5, "volume": 0.2}
	drums[39] = {"sound": "@sfx-missile", "note": 4, "volume": 0.3}
	drums[40] = {"sound": "@sfx-flame2", "note": 1.5, "volume": 0.2}
	drums[41] = {"sound": "@sfx-dullExplosion", "note": 1.5, "volume": 0.3}
	drums[42] = {"sound": "@sfx-sap", "note": 4, "volume": 0.3}
	drums[43] = {"sound": "@sfx-dullExplosion", "note": 2, "volume": 0.3}
	drums[44] = {"sound": "@sfx-sap", "note": 2.5, "volume": 0.3}
	drums[45] = {"sound": "@sfx-dullExplosion", "note": 2.5, "volume": 0.3}
	drums[46] = {"sound": "@sfx-flame2", "note": 1.5, "volume": 0.3}
	drums[47] = {"sound": "@sfx-dullExplosion", "note": 3, "volume": 0.3}
	drums[48] = {"sound": "@sfx-dullExplosion", "note": 3.5, "volume": 0.3}
	drums[49] = {"sound": "@sfx-flame2", "note": 1.5, "volume": 0.3}
	drums[50] = {"sound": "@sfx-dullExplosion", "note": 4, "volume": 0.3}

	for v in drum_overrides:
		drums[v["drum_id"]] = {"sound": v["sound"], "note": v["pitch"], "volume": v["volume"]}

	for drum in drums:
		drum["volume"] = drum["volume"] * vol_mod

	return drums

def midi_to_note_list(file, programs, drums):
	# bad code, but it works, so i probably won't fix it
	try:
		mid = mido.MidiFile(file)
	except OSError:
		GLOBAL_ERROR(f"File '{file}' not found, or bad file. Try --help.")

	channels = [{"program": 0, "pan": 0} for x in range(16)]
	notes = []
	tempo = 500000
	for i, track in enumerate(mid.tracks):
		note_states = []
		for j in range(128):
			note_states.append({"state": "note_off", "start_time": 0, "velocity": 64})
		time = 0
		for msg in track:
			time += mido.tick2second(msg.time, mid.ticks_per_beat, tempo)*1000
			if msg.type == "note_on" and note_states[msg.note]["state"] == "note_off":
				note_states[msg.note]["state"] = "note_on"
				note_states[msg.note]["velocity"] = msg.velocity
				note_states[msg.note]["start_time"] = time
				note_states[msg.note]["program"] = channels[msg.channel]["program"]
			elif (msg.type == "note_off" and note_states[msg.note]["state"] == "note_on") or (msg.type == "note_on" and msg.velocity == 0):
				note_states[msg.note]["state"] = "note_off"
				if msg.channel != 9 and programs[note_states[msg.note]["program"]]["loop"] == True:
					length = programs[note_states[msg.note]["program"]]["length"] / (2**((msg.note - programs[note_states[msg.note]["program"]]["note"]) / 12))
					for loop_time in frange(note_states[msg.note]["start_time"], max(note_states[msg.note]["start_time"] + length, time - length), length):
						notes.append({
							"note": msg.note,
							"program": note_states[msg.note]["program"],
							"channel": msg.channel,
						 	"velocity": note_states[msg.note]["velocity"],
						 	"pan": channels[msg.channel]["pan"],
						 	"start_time": loop_time
						})
				else:
					notes.append({
						"note": msg.note,
						"program": note_states[msg.note]["program"],
						"channel": msg.channel,
					 	"velocity": note_states[msg.note]["velocity"],
					 	"pan": channels[msg.channel]["pan"],
					 	"start_time": note_states[msg.note]["start_time"]
					})
			elif msg.type == "program_change":
				channels[msg.channel]["program"] = msg.program
			elif msg.type == "set_tempo":
				tempo = msg.tempo
			elif msg.type == "control_change":
				if msg.control == 10:
					channels[msg.channel]["pan"] = (msg.value - 64)/64

	return sorted(notes, key=lambda x: x["start_time"])

def note_list_to_proc_list(note_list, args, programs, drums):
	procs = [init_default_proc()]

	increment = 0

	for note in note_list:
		for proc in procs:
			if note["start_time"] > proc["end_time"] and proc["note_count"] < (230 if args.vfx else 320):
				proc = append_note_proc(proc, note, args, programs, drums, increment)
				increment += 1
				break
		else:
			procs.append(append_note_proc(init_default_proc(), note, args, programs, drums, increment))
			increment += 1

	return procs

def init_default_proc():
	return {"code": "setrate 1000\nsensor enable switch1 @enabled\n jump 1 notEqual enable true\nset start_time @time\n", "end_time": -1, "note_count": 0}

def append_note_proc(proc, note, args, programs, drums, increment):
	proc["code"] += f"op add wait_time start_time {note["start_time"]}\n"
	proc["code"] += f"Label{increment}:\n"
	proc["code"] += f"jump Label{increment} lessThan @time wait_time\n"

	#not ideal, but the best idea i could come up with
	proc["code"] = try_add_code_effect_note(proc["code"], note, args)
	proc["code"] = try_add_code_effect_drum(proc["code"], note, args)
	proc["code"] = try_add_code_sound_note_global(proc["code"], note, programs, args)
	proc["code"] = try_add_code_sound_drum_global(proc["code"], note, drums, args)
	proc["code"] = try_add_code_sound_note_positional(proc["code"], note, programs, args)
	proc["code"] = try_add_code_sound_drum_positional(proc["code"], note, drums, args)

	proc["end_time"] = note["start_time"] + 50
	proc["note_count"] += 1
	return proc

def try_add_code_effect_note(code, note, args):
	if(args.vfx and note["channel"] != 9):
		return code + f"effect wave {args.positional_pos[0]} {args.positional_pos[1]} 1.5 {'%%%02x%02x%02x' % hsv2rgb(note["note"]/127, 1, 1)}\n"
	else:
		return code

def try_add_code_effect_drum(code, note, args):
	if(args.vfx and note["channel"] == 9):
		return code + f"effect placeBlock {args.positional_pos[0]} {args.positional_pos[1]} 1\n"
	else:
		return code

def try_add_code_sound_note_global(code, note, programs, args):
	if(note["channel"] != 9 and not args.positional):
		return code + f"playsound false {programs[note["program"]]["sound"]} {(note["velocity"]/127) * 2 * programs[note["program"]]["volume"]} {2**((note["note"] - programs[note["program"]]["note"]) / 12)} {note["pan"]} 0 0 {int(args.limit)}\n"
	else:
		return code

def try_add_code_sound_drum_global(code, note, drums, args): 
	if(note["channel"] == 9 and not args.positional):
		return code + f"playsound false {drums[note["note"]]["sound"]} {(note["velocity"]/127) * 2 * drums[note["note"]]["volume"]} {drums[note["note"]]["note"]} {note["pan"]} 0 0 {int(args.limit)}\n"
	else:
		return code

def try_add_code_sound_note_positional(code, note, programs, args):
	if(note["channel"] != 9 and args.positional):
		return code + f"playsound true {programs[note["program"]]["sound"]} {(note["velocity"]/127) * 2 * programs[note["program"]]["volume"]} {2**((note["note"] - programs[note["program"]]["note"]) / 12)} 0 {args.positional_pos[0]} {args.positional_pos[1]} {int(args.limit)}\n"
	else:
		return code

def try_add_code_sound_drum_positional(code, note, drums, args): 
	if(note["channel"] == 9 and args.positional):
		return code + f"playsound true {drums[note["note"]]["sound"]} {(note["velocity"]/127) * 2 * drums[note["note"]]["volume"]} {drums[note["note"]]["note"]} 0 {args.positional_pos[0]} {args.positional_pos[1]} {int(args.limit)}\n"
	else:
		return code

def proc_list_to_schem(proc_list, args):
	schem = Schematic()
	schem.set_tag('name', args.file if len(args.file.rsplit("/", 1)) == 1 else args.file.rsplit("/", 1)[1])
	schem.set_tag('description', 'An auto generated midi schematic\nOnly works in BE\n\nBy SkyeTheFoxyFox')

	for i, proc in enumerate(proc_list):
		square_size = math.ceil(math.sqrt(len(proc_list) + 1))
		x = (i + 1) % square_size
		y = - ((i + 1) // square_size)
		schem.add_block(Block(Content.WORLD_PROCESSOR, x, y, ProcessorConfig(proc["code"], [ProcessorLink(-x, -y, "switch1")]).compress(), 0))

	schem.add_block(Block(Content.SWITCH, 0, 0, False, 0))
	return schem

def frange(x, y, jump):
  while x < y:
    yield x
    x += jump

def hsv2rgb(h,s,v):
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))

args = Arguments(sys.argv)
if args.file == "":
	GLOBAL_ERROR("Source file path required")

programs = get_programs(args.prog_overrides, args.note_vol_mod)
drums = get_drums(args.drum_overrides, args.drum_vol_mod)

note_list = midi_to_note_list(args.file, programs, drums)
proc_list = note_list_to_proc_list(note_list, args, programs, drums)
schem = proc_list_to_schem(proc_list, args)

if args.copy:
	schem.write_clipboard()
if args.out_file != "":
	schem.write_file(args.out_file)

print("done")