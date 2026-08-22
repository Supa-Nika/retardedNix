# NixOS + niri + DankMaterialShell

A from-scratch, flake-based NixOS desktop: [niri](https://github.com/YaLTeR/niri)
(scrollable-tiling Wayland compositor) as the compositor, and
[DankMaterialShell](https://github.com/AvengeMedia/DankMaterialShell) (DMS) as
the panel / launcher / notifications / OSD shell, all launched through
`greetd` + `tuigreet`.

## Layout

```
flake.nix                               # inputs + nixosConfigurations
hosts/desktop/configuration.nix         # system config (boot, greetd, audio, fonts...)
hosts/desktop/hardware-configuration.nix# PLACEHOLDER — replace with your own
home/home.nix                           # home-manager: DMS + niri config wiring
home/niri/config.kdl                    # niri compositor config + keybinds
```

niri itself comes straight from nixpkgs (`programs.niri.enable`), **not**
from `niri-flake` — as of nixpkgs 26.05 that's the recommended path and
avoids a known version mismatch between niri-flake's stable package and the
niri version DMS expects.

## Before you build

1. **Set your username/hostname.** Edit `hostname` and `username` at the top
   of `flake.nix` (defaults: `nixos-niri` / `user`).

2. **Generate real hardware config.** `hosts/desktop/hardware-configuration.nix`
   is a placeholder. From a running NixOS installer (after partitioning /
   mounting your target disks), run:

   ```bash
   nixos-generate-config --root /mnt --show-hardware-config > hosts/desktop/hardware-configuration.nix
   ```

   or, on an already-installed system:

   ```bash
   sudo nixos-generate-config --show-hardware-config > hosts/desktop/hardware-configuration.nix
   ```

3. **Timezone/locale** — `hosts/desktop/configuration.nix` defaults to
   `Europe/Warsaw`; change `time.timeZone` if needed.

4. If you're on a laptop, you may also want `services.libinput.enable` tweaks,
   TLP/power-profiles tuning, etc. — not included here to keep this generic.

## Install / apply

For a fresh install (from the NixOS installer, with disks already
partitioned/mounted at `/mnt`):

```bash
sudo nixos-install --root /mnt --flake .#nixos-niri
```

On an existing NixOS system, copy this directory to `/etc/nixos` (or
anywhere) and run:

```bash
sudo nixos-rebuild switch --flake .#nixos-niri
```

## After first boot

- Log in through the tuigreet prompt; it starts `niri-session` for you.
- DMS starts automatically as a user systemd service. If anything's off,
  check it with:

  ```bash
  dms doctor -v
  ```

  This tells you about any missing fonts/dependencies for your exact setup.

- Default niri keybinds (see `home/niri/config.kdl` for the full list):
  - `Mod+Return` — terminal (`foot`)
  - `Mod+D` — DMS app launcher (Spotlight)
  - `Mod+Space` — DMS Spotlight Bar (compact inline search)
  - `Mod+N` — notifications
  - `Mod+M` — control center (network/bluetooth/audio)
  - `Mod+V` — clipboard history
  - `Mod+I` — DMS settings
  - `Mod+L` — lock screen
  - `Mod+Escape` — power menu
  - `Print` — interactive screenshot
  - `Mod+1..5` — switch workspace, `Mod+Shift+1..5` — move window to workspace
  - `Mod+Shift+E` — quit niri

## Customizing DMS

Widget/panel behavior is normally tweaked live from DMS's own settings UI
(`Mod+I`), but since we set `home-manager` to manage `settings`/`session`,
GUI changes will show as "read-only" — copy them via DMS's `json2nix` helper
and paste the result into `home/home.nix` under
`programs.dank-material-shell.settings` to keep it declarative. See the
[DMS NixOS flake docs](https://danklinux.com/docs/dankmaterialshell/nixos-flake)
for the full option reference (plugins, clipboard settings, etc.).

## Notes / things you may want to add later

- **Plugins**: DMS has a plugin registry flake
  (`github:AvengeMedia/dms-plugin-registry`) for declarative plugin installs.
- **Multiple hosts**: duplicate `hosts/desktop` as `hosts/laptop`, etc., and
  add another `nixosConfigurations.<name>` entry in `flake.nix`.
- **Unfree packages** (e.g. proprietary GPU drivers): flip
  `nixpkgs.config.allowUnfree = true;` in `hosts/desktop/configuration.nix`.
