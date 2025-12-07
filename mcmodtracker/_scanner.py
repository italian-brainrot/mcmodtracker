import argparse
import glob
import os
import zipfile


def is_mcreator_mod(jar_path) -> tuple[bool, str]:
    """
    Analyzes a .jar file to determine if it was likely made with MCreator.
    Returns a tuple: (Boolean, Reason_String)
    """
    try:
        with zipfile.ZipFile(jar_path, 'r') as jar:
            file_list = jar.namelist()

            # METHOD 1: Check for Default Package Structure
            # MCreator often defaults to 'net.mcreator.modid'
            for file in file_list:
                if file.startswith('net/mcreator/'):
                    return True, "Found 'net/mcreator' package structure"

            # METHOD 2: Check Metadata (mods.toml / neoforge.mods.toml)
            # Modern NeoForge/Forge mods use TOML files for metadata.
            toml_files = [f for f in file_list if f.endswith('mods.toml') and 'META-INF' in f]

            for toml_file in toml_files:
                try:
                    with jar.open(toml_file) as f:
                        content = f.read().decode('utf-8', errors='ignore')

                        # Check 2a: Explicit Credits
                        # MCreator auto-generates: credits="Created using mod maker MCreator - https://mcreator.net/about"
                        if 'Created using mod maker MCreator' in content:
                            return True, "Found MCreator credit in metadata"

                        # Check 2b: Display URL
                        # Default URL often points to mcreator.net
                        if 'displayURL="https://mcreator.net' in content:
                            return True, "displayURL points to mcreator.net"

                except Exception:
                    continue

    except zipfile.BadZipFile:
        return False, "bad file"

    return False, "no mc creator"



def uses_mcfunction(jar_path) -> bool:
    try:
        # Open the JAR as a ZIP file
        with zipfile.ZipFile(jar_path, "r") as zip_ref:
            # Get list of all files inside the JAR
            files_inside = zip_ref.namelist()

            # Check if any file inside matches the pattern
            for filename in files_inside:
                if ".mcfunction" in filename:
                    return True

    except zipfile.BadZipFile:
        return False
    return False