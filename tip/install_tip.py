import os
import subprocess


def create_tip_dir():
    tip_dir = os.path.join(os.path.expanduser('~'), 'tip')
    print(f"""
    TIP will now be installed into this location:

    {tip_dir}

    - Press ENTER to confirm the location
    - Press CTRL-C to abort the installation
    - Or specify a different location below
    """)
    while True:
        new_location = input(f"[{tip_dir}] >>>").strip()
        if new_location == "":
            break
        os.makedirs(new_location, exist_ok=True)
        tip_dir = new_location
    return tip_dir


def install_tip():
    subprocess.run(["python", "-m", "pip", "install", "-e", "../../"])
    print("TIP installed")


def init_config(tip_dir):
    from tip.config import pass_config

    @pass_config
    def change_config(tip_dir, config):
        config['tip_dir'] = tip_dir
        config['active_environment_name'] = config.get('active_environment_name', 'base')

    change_config(tip_dir)
    print("Config saved")


def ensure_base_exists(tip_dir):
    from tip import environment
    base_path = environment.get_environment_path(tip_dir, "base")
    if not os.path.exists(base_path):
        environment.save_environment({}, base_path)


if __name__ == "__main__":
    tip_dir = create_tip_dir()
    install_tip()
    init_config(tip_dir)
    ensure_base_exists(tip_dir)
