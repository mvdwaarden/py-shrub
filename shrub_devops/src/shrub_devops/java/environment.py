import os
import json
import argparse
from pathlib import Path
from shrub_devops.template.build_object import BuildObject

# JVENV_HOME = Path.home() / ".jvenv"
#
#
#
# def ensure_home():
#     JVENV_HOME.mkdir(exist_ok=True)
#
# def env_path(name):
#     return JVENV_HOME / name
#
# def create_env(name, jdk, maven=None, gradle=None):
#     ensure_home()
#     env_dir = env_path(name)
#     bin_dir = env_dir / "bin"
#     bin_dir.mkdir(parents=True, exist_ok=True)
#
#     config = {
#         "jdk": jdk,
#         "maven": maven,
#         "gradle": gradle
#     }
#
#     with open(env_dir / "config.json", "w") as f:
#         json.dump(config, f, indent=2)
#
#     # generate activate/deactivate scripts
#     (bin_dir / "activate").write_text(generate_activate_script(config))
#     (bin_dir / "deactivate").write_text(generate_deactivate_script())
#
#     os.chmod(bin_dir / "activate", 0o755)
#     os.chmod(bin_dir / "deactivate", 0o755)
#
#     print(f"✅ Created jvenv: {name}")
#     print(f"👉 To activate: source {bin_dir}/activate")
#
# def generate_activate_script(config):
#     return f"""#!/usr/bin/env bash
# # Activate jvenv
#
# export OLD_PATH="$PATH"
# export OLD_JAVA_HOME="$JAVA_HOME"
#
# export JAVA_HOME="{config['jdk']}"
# {"export M2_HOME=\"" + config['maven'] + "\" && export PATH=\"$M2_HOME/bin:$PATH\"" if config.get('maven') else ""}
# {"export GRADLE_HOME=\"" + config['gradle'] + "\" && export PATH=\"$GRADLE_HOME/bin:$PATH\"" if config.get('gradle') else ""}
# export PATH="$JAVA_HOME/bin:$PATH"
#
# echo "Activated jvenv:"
# echo "  JAVA_HOME=$JAVA_HOME"
# java -version
# """
#
# def generate_deactivate_script():
#     return """#!/usr/bin/env bash
# # Deactivate jvenv
#
# export PATH="$OLD_PATH"
# export JAVA_HOME="$OLD_JAVA_HOME"
# unset OLD_PATH OLD_JAVA_HOME
# echo "Deactivated jvenv."
# """
#
# def list_envs():
#     ensure_home()
#     envs = [p.name for p in JVENV_HOME.iterdir() if p.is_dir()]
#     print("Available environments:")
#     for e in envs:
#         print(f"  - {e}")
#
# def main():
#     parser = argparse.ArgumentParser(description="Manage isolated Java environments.")
#     sub = parser.add_subparsers(dest="command")
#
#     create = sub.add_parser("create", help="Create a new jvenv")
#     create.add_argument("name")
#     create.add_argument("--jdk", required=True, help="Path or version of JDK")
#     create.add_argument("--maven", help="Path to Maven")
#     create.add_argument("--gradle", help="Path to Gradle")
#
#     sub.add_parser("list", help="List all jvenvs")
#
#     args = parser.parse_args()
#
#     if args.command == "create":
#         create_env(args.name, args.jdk, args.maven, args.gradle)
#     elif args.command == "list":
#         list_envs()
#     else:
#         parser.print_help()
#
# if __name__ == "__main__":
#     main()


class Environment(BuildObject):
    def __init__(self, name: str, description: str, environment_type: str, **kwargs):
        super().__init__()
        self.name = name
        self.description = description
        self.environment_type = environment_type
        self.environment_dir = os.path.join(os.getcwd(), self.name)
        self.maven = kwargs['maven'] if 'maven' in kwargs else ''
        self.jdk = kwargs['jdk'] if 'jdk' in kwargs else ''
        self.gradle = kwargs['gradle'] if 'gradle' in kwargs else ''
        self.environment_variables = ["PATH", "JAVA_HOME", "GRADLE_HOME", "MAVEN_HOME" ]

    def create(self):
        self.clone_directory("jvenv")


