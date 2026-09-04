#!/usr/bin/env python3
import os
import sys
import shutil
import argparse

def main():
    parser = argparse.ArgumentParser(description="Install a skill to ARIA_SKILLS_PATH")
    parser.add_argument("skill_name", help="Name of the skill to install")
    parser.add_argument("--dest", default=os.environ.get("ARIA_SKILLS_PATH"), 
                        help="Destination ARIA_SKILLS_PATH (defaults to env var)")
    args = parser.parse_args()

    if not args.dest:
        print("Error: ARIA_SKILLS_PATH is not set and --dest is not provided.")
        sys.exit(1)

    skill_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", args.skill_name)
    
    if not os.path.exists(skill_src):
        print(f"Error: Skill '{args.skill_name}' not found in the catalog.")
        sys.exit(1)
        
    dest_path = os.path.join(args.dest, args.skill_name)
    
    if os.path.exists(dest_path):
        print(f"Skill '{args.skill_name}' already exists at {dest_path}. Overwriting...")
        shutil.rmtree(dest_path)
        
    shutil.copytree(skill_src, dest_path)
    print(f"Successfully installed '{args.skill_name}' to {dest_path}")

if __name__ == "__main__":
    main()
