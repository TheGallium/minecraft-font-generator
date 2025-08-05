# type: ignore[reportOptionalSubscript]

from requests import get
from pathlib import Path
from plistlib import dump as plist_dump
from unicodedata import name as unicode_name
from sys import argv, version_info, executable
from re import sub
from json import load as json_load
import os, socket

if version_info[0] < 3 or version_info[0] >= 3 and version_info[1] < 8:
	print("The required minimum version is Python 3.8!")
	exit(1)

def internet(host="8.8.8.8", port=53, timeout=3, show_exeption=False):
		"""
		Check if an internet connection is available.
		Returns a boolean.
		"""
		try:
			socket.setdefaulttimeout(timeout)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
			return True
		except socket.error as ex:
			if show_exeption:
				print(ex)
			return False



def download():
	""" STEP 1 """

	if not internet():
		print("Cannot download assets!\nAn internet connection is required!")

	print("""
 Downloading font files from:
 "https://mcasset.cloud/

 Special assets are from:
 "https://minecraft.wiki/"

 Calculating size...
	""")

	# Special assets are additional textures that are not in game.
	# Format: `{"name without extention": "url to download"}`
	special_downloads = [
		{"notdef": "https://minecraft.wiki/images/Missing_Glyph_JE4.png"}
	]

	mc_asset_base_url = "https://assets.mcasset.cloud/latest"

	fonts_images = get(f"{mc_asset_base_url}/assets/minecraft/textures/font/_list.json")
	fonts_images = fonts_images.json()["files"]
	fonts_images_skip = [font for font in fonts_images if not font.lower().endswith(".png")]

	fonts_map = get(f"{mc_asset_base_url}/assets/minecraft/font/_list.json")
	fonts_map = fonts_map.json()["files"]
	fonts_map_skip = [font for font in fonts_map if not font.lower().endswith(".json")]

	fonts_include = get(f"{mc_asset_base_url}/assets/minecraft/font/include/_list.json")
	fonts_include = fonts_include.json()["files"]
	fonts_include_skip = [font for font in fonts_include if not font.lower().endswith(".json")]

	skipped = len(fonts_images_skip) + len(fonts_map_skip) + len(fonts_include_skip)

	n_special = len(special_downloads)
	n = len(fonts_images) + len(fonts_map) + len(fonts_include) + n_special
	print(f" {n-skipped} files to download")
	print(f" - {len(fonts_images)} textures (+{n_special} special)")
	print(f" - {len(fonts_map) + len(fonts_include)} maps")
	print(f" - ({skipped} skipped)\n")

	for font in fonts_images:
		if not font.lower().endswith(".png"):
			continue
		download_url = f"{mc_asset_base_url}/assets/minecraft/textures/font/{font}"
		print(f"Downloading: '{download_url}'")
		response = get(download_url)
		font_path = Path(f"assets/font/texture/{font}")
		font_path.parent.mkdir(parents=True, exist_ok=True)
		with open(font_path, "wb") as file:
			file.write(response.content)

	print()
	for font in fonts_map:
		if not font.lower().endswith(".json"):
			continue
		download_url = f"{mc_asset_base_url}/assets/minecraft/font/{font}"
		print(f"Downloading: '{download_url}'")
		response = get(download_url)
		font_path = Path(f"assets/font/map/{font}")
		font_path.parent.mkdir(parents=True, exist_ok=True)
		with open(font_path, "wb") as file:
			file.write(response.content)

	for font in fonts_include:
		if not font.lower().endswith(".json"):
			continue
		download_url = f"{mc_asset_base_url}/assets/minecraft/font/include/{font}"
		print(f"Downloading: '{download_url}'")
		response = get(download_url)
		font_path = Path(f"assets/font/map/include/{font}")
		font_path.parent.mkdir(parents=True, exist_ok=True)
		with open(font_path, "wb") as file:
			file.write(response.content)

	print()
	for special in special_downloads:
		for key, url in special.items():
			extention = url.split(".")[-1]
			print(f"Special: '{url}' as 'special/{key}.{extention}'")
			response = get(url)
			font_path = Path(f"assets/font/texture/special/{key}.{extention}")
			font_path.parent.mkdir(parents=True, exist_ok=True)
			with open(font_path, "wb") as file:
				file.write(response.content)



def make_ufo():
	""" STEP 2 """

	# Customisation
	font_name = "default"
	scale = 100

	try:
		from PIL import Image
	except ImportError:
		if not internet():
			print("You need an Internet connection to install the Pillow module\nPlease install it manually.")
			exit(1)

		print("Pillow is not installed. Installing now...\n\n")
		os.system(f"{executable} -m pip install Pillow")
		try:
			from PIL import Image
		except ImportError:
			print("\n\nFailed to install the Pillow module!\nPlease install it manually.")
			exit(1)
		else:
			print("Pillow installed successfully.\n\n")



	xml_header = '<?xml version="1.0" encoding="UTF-8"?>'

	ufo_path = Path("assets/font/ufo/default.ufo")
	ufo_path.mkdir(parents=True, exist_ok=True)

	glyphs_path = Path(ufo_path, "glyphs")
	glyphs_path.mkdir(parents=True, exist_ok=True)

	map_path = Path(f"assets/font/map/")
	font_path = Path(f"assets/font/texture")

	with open(Path(ufo_path, "metainfo.plist"), "wb") as f:
		plist_dump({"creator": "com.mojang.minecraft", "formatVersion": 3}, f)

	with open(Path(ufo_path, "layercontents.plist"), "wb") as f:
		plist_dump([["public.default", "glyphs"]], f)


	def load(file):
		chars = {}
		spacing = {}
		sizing = {}

		with open(file, "r") as f:
			content = json_load(f)
			for provider in content["providers"]:
				if provider["type"] == "reference":
					included = provider["id"].split(":")[1]
					sub_chars, sub_spacing, sub_sizing = load(Path(map_path, included+".json"))
					chars.update(sub_chars)
					spacing.update(sub_spacing)
					sizing.update(sub_sizing)
				elif provider["type"] == "bitmap":
					font_image = provider["file"]
					font_image = provider["file"].split(":")[1]
					bitmap_chars = provider["chars"]
					ascent = provider["ascent"]
					try:
						height = provider["height"]
						sizing.update(({font_image: [ascent, height]}))
					except KeyError:
						sizing.update(({font_image: [ascent, 8]}))

					chars_list = ""
					for line in bitmap_chars:
						for char in line:
							chars_list += char
						chars_list += "\n"
					chars.update({font_image: chars_list})
				elif provider["type"] == "space":
					advances = provider["advances"]
					spacing.update(advances)

		return chars, spacing, sizing

	print("Loading assets...")
	chars, spacing, sizing = load(Path(map_path, f"{font_name}.json"))



	max_ascent = 0
	max_descent = 0
	for file, (ascent, height) in sizing.items():
		print(f"File: {file}, ascent: {ascent}, height: {height}")
		if ascent > max_ascent:
			max_ascent = ascent
		descent = height - ascent
		if descent > max_descent:
			max_descent = descent

	print(f"Max ascent: {max_ascent}, Max descent: {max_descent}")

	fontinfo = {
		"familyName": font_name,
		"styleName": "Regular",
		"unitsPerEm": 1000,
		"ascender": max_ascent * scale,
		"descender": -max_descent * scale,
	}

	with open(Path(ufo_path, "fontinfo.plist"), "wb") as f:
		plist_dump(fontinfo, f)


	def get_char_image(search, chars, sizing):
		def find_in_chars(search, chars):
			for file in chars:
				content = chars[file].split("\n")
				line_n = 0
				for line in content:
					if search in line:
						i = 0
						for char in line:
							if char == search:
								found_file = file
								pos = [line_n, i]
								return (found_file, pos)
							i += 1
					line_n += 1
			return (None, None)
		
		result = find_in_chars(search, chars)
		if result == (None, None):
			return None

		found_file = result[0] 
		file = Path(found_file).name
		pos = result[1]

		if pos is None:
			return None

		image = Image.open(Path(font_path, file))
		char_width = image.size[0] / 16
		char_height = sizing[found_file][1]
		left = pos[1] * char_width
		upper = pos[0] * char_height
		right = left + char_width
		lower = upper + char_height
		image = image.crop((left, upper, right, lower))
		return image, found_file



	def generate_glif(img_or_path, i, source_file=None):
		if isinstance(img_or_path, (str, Path)):
			char = Image.open(img_or_path)
		else:
			char = img_or_path
		char = char.transpose(Image.FLIP_TOP_BOTTOM)

		found_file = None
		if source_file is not None:
			found_file = Path(source_file).name
		elif isinstance(img_or_path, (str, Path)):
			found_file = Path(img_or_path).name
		else:
			for file, chars_string in chars.items():
				if chr(i) in chars_string:
					found_file = Path(file).name
					break

		ascent, height = sizing.get(found_file, (max_ascent, max_ascent + max_descent))
		offset_y = (max_ascent - ascent) * scale

		pixels = char.load()
		w, h = char.size

		bounding_box = char.getbbox(alpha_only = False)
		advance_pixels = (bounding_box[2] - bounding_box[0]) + 1

		glyph_data = ""
		character, decimal_value, hex_value = None, None, None
		if type(i) is int:
			try:
				character = chr(i)
			except (ValueError, TypeError):
				character = ""
			decimal_value = i
			hex_value = hex(i)[2:].upper()
			glyph_name = unicode_name(character, character)
		else:
			glyph_name = sub(r'[^\w.-]', '_', str(i))

		for y in range(h):
			for x in range(w):
				pixel = pixels[x, y]
				if isinstance(pixel, int): # L
					lum = pixel
				elif len(pixel) == 2: # LA
					lum, alpha = pixel
				elif len(pixel) == 3: # RGB
					r, g, b = pixel
					lum = int((r + g + b) / 3)
				elif len(pixel) == 4: # RGBA
					r, g, b, a = pixel
					lum = int((r + g + b) / 3)
				else:
					lum = 0  # Fallback
				
				if offset_y != 0:
					print(offset_y)

				if lum > 0.5:
					glyph_data += '<contour>' + \
						f'<point x="{(x*scale)+scale/2}" y="{(y*scale)+offset_y}" type="line" />' + \
						f'<point x="{(x*scale)+scale/2}" y="{((y+1)*scale)+offset_y}" type="line" />' + \
						f'<point x="{((x+1)*scale)+scale/2}" y="{((y+1)*scale)+offset_y}" type="line" />' + \
						f'<point x="{((x+1)*scale)+scale/2}" y="{(y*scale)+offset_y}" type="line" />' + \
						'</contour>'

		xml_unicode_tag = ""
		if type(i) is int:
			xml_unicode_tag = f'<unicode hex="{hex_value}" />'
		xml_glyph_tag = f'<glyph name="{glyph_name}" format="2">'
		glyph_content = xml_header + \
			xml_glyph_tag + \
			xml_unicode_tag + \
			f'<advance width="{advance_pixels*scale}" />' + \
			'<outline>' + \
			glyph_data + \
			'</outline>' + \
			'</glyph>'

		return {                     #     --- Example: ---
			"content": glyph_content, # (XML content of the glyph)
			"name": glyph_name,       # LATIN CAPITAL LETTER A
			"string": character,      # "A" (unused)
			"decimal": decimal_value, # 65 
			"hex": hex_value,         # "41" (unused)
		}

	# Make custom chars with special assets
	glyphs = [{
		"name": "notdef",
		"string": None,
		"decimal": "notdef",
		"hex": None,
		"content": generate_glif("assets/font/texture/special/notdef.png", ".notdef")["content"]
	}]

	print("Getting all glyphs images...")
	for char in "".join(chars.values()):
		if char.strip() == "":
			continue
		result = get_char_image(char, chars, sizing)
		if result is None:
			continue
		img, found_file = result
		if img is None or img.getbbox() is None:
			continue
		glif = generate_glif(img, ord(char), found_file)
		glyphs.append(glif)



	print("Vectorizing images...")
	glyphs_dict = {".notdef": "notdef.glif"}
	for glyph in glyphs:
		filename = f"{glyph['decimal']}.glif" if isinstance(glyph['decimal'], int) else f"{glyph['name']}.glif"
		glif_file = Path(glyphs_path, filename)
		with open(glif_file, "wb") as f:
			f.write(glyph["content"].encode("utf-8"))
		key = sub(r'[^\w.-]', '_', glyph["name"])
		glyphs_dict[key] = glif_file.name

	with open(Path(glyphs_path, "contents.plist"), "wb") as f:
		plist_dump(glyphs_dict, f)



def compile_font():
	""" STEP 3 """
	print()



def make_choice(choice):

	aliases = {
		"exit": -1,
		"all": 0,
		"everything": 0,
		"download": 1,
		"dl": 1,
		"ufo": 2,
		"make_ufo": 2,
		"compile": 3,
		"make_font": 3
	}
	if choice in aliases:
		choice = aliases[choice]

	if choice == -1:
		os.system('cls' if os.name == 'nt' else 'clear')
		exit(0)
	elif choice == 1:
		download()
	elif choice == 2:
		make_ufo()
	elif choice == 3:
		compile_font()
	elif choice == 0:
		download()
		print(f"\n{"–"*16}\n")
		make_ufo()
		print(f"\n{"–"*16}\n")
		compile_font()
	else:
		return False

# Arguments will come soon!

# if len(argv) > 1:
# 	correct_arg = make_choice(argv[2])
# 	if correct_arg == False:
# 		incorrect_args = True
# 	else:
# 		if len(argv) > 2:
# 			dash_args = argv
# 			dash_args.pop(0)
# 			dash_args.pop(1)
# 			if "--continue" not in dash_args or "-c" not in dash_args:
# 				os.system('cls' if os.name == 'nt' else 'clear')
# 				exit(0)



def check_steps():
	"""
	Rudimentary check of the state of the 3 steps of this program.  
	Also algorithmically recommands a step and warns the user about steps  
	that can't be completed due to relying on the output of a previous step.
	"""

	def is_filled(path):
		"""
		Returns True if the content of the folder provided  
		in `path` exists and contains something.
		"""
		return path.exists() and any(path.iterdir())
	
	step0text, step1text, step2text, step3text = "", "", "", ""

	done1 = is_filled(Path("assets/font/texture")) and is_filled(Path("assets/font/map")) and is_filled(Path("assets/font/map/include"))
	done2 = is_filled(Path("assets/font/ufo/"))
	done3 = is_filled(Path("assets/font/generated_fonts"))

	if not done1:
		step2text = "(Previous step missing!)"
	if not done2:
		step3text = "(Previous step missing!)"
	if done1 and not done2:
		step2text = "(Recommended)"
	elif done2 and not done3:
		step3text = "(Recommended)"
	elif all([not done1, not done2, not done3]):
		step0text = "(Recommended)"
	elif all([done1, done2, done3]):
		step0text = "(Recommended)"

	if not internet():
		step0text, step1text = "(Internet connection required!)", "(Internet connection required!)"

	return step0text, step1text, step2text, step3text

while True:
	choice = None
	last_choice = ""
	while choice is None or not (0 <= int(choice) <= 3):
		os.system('cls' if os.name == 'nt' else 'clear')
		step0text, step1text, step2text, step3text = check_steps()

		print(f"""
 Welcome to Gallium's bitmap font converter.
 What would you like to start with?

 Type a number to execute the corresponding step.
   0: Do everything! {step0text}
   1: Download assets {step1text}
   2: Make UFO folder {step2text}
   3: Compile font {step3text}
   Press enter to exit.
""")
		if choice == "exit":
			os.system('cls' if os.name == 'nt' else 'clear')
			exit(0)
		elif choice != None:
			print(f" '{last_choice}' is an invalid choice!")
		else:
			print()
		incorrect_args = False
		if incorrect_args == True:
			print("The provided arguments are incorrect!")

		choice = input(" > ")
		choice = choice.strip()
		if choice == "":
			os.system('cls' if os.name == 'nt' else 'clear')
			exit(0)
		last_choice = choice
		try:
			choice = int(choice)
		except ValueError:
			choice = 999
	os.system('cls' if os.name == 'nt' else 'clear')


	make_choice(choice)

exit(0)
