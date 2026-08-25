{ config, pkgs, lib, username, hostname, ... }:
let
  obs-face-tracker = pkgs.stdenv.mkDerivation rec {
    pname = "obs-face-tracker";
    version = "0.9.1";

    src = pkgs.fetchFromGitHub {
      owner = "norihiro";
      repo = "obs-face-tracker";
      rev = version;
      hash = "sha256-mlbzuXcXyw3DVPKl0sZZfLNXj9plF4pYQg+DGzKqTxw=";
      fetchSubmodules = true;
    };

    nativeBuildInputs = [ 
      pkgs.cmake
      pkgs.pkg-config
      pkgs.qt6.wrapQtAppsHook
    ];

    buildInputs = [
      pkgs.obs-studio
      pkgs.dlib
      pkgs.openblas
      pkgs.opencv
      pkgs.qt6.qtbase
      pkgs.qt6.qt5compat
    ];

    # Patch CMake to explicitly locate GuiPrivate before target_link_libraries runs
    preConfigure = ''
      substituteInPlace CMakeLists.txt \
        --replace-fail 'Core Gui' 'Core Gui GuiPrivate'
    '';

    cmakeFlags = [
      "-DCMAKE_INSTALL_PREFIX=${placeholder "out"}"
      "-DQT_VERSION=6"
    ];

    postInstall = ''
      # 1. Move binary into lib/obs-plugins/
      mkdir -p $out/lib/obs-plugins
      if [ -d "$out/obs-plugins/64bit" ]; then
        mv $out/obs-plugins/64bit/*.so $out/lib/obs-plugins/
        rm -rf $out/obs-plugins
      elif [ -f "$out/bin/64bit/obs-face-tracker.so" ]; then
        mv $out/bin/64bit/*.so $out/lib/obs-plugins/
      fi

      # 2. Extract locale files into share/obs/obs-plugins/obs-face-tracker/
      mkdir -p $out/share/obs/obs-plugins/obs-face-tracker
      if [ -d "$out/data/obs-plugins/obs-face-tracker" ]; then
        cp -r $out/data/obs-plugins/obs-face-tracker/* $out/share/obs/obs-plugins/obs-face-tracker/
        rm -rf $out/data
      elif [ -d "$out/share/obs/obs-plugins/obs-face-tracker/obs-plugins/obs-face-tracker" ]; then
        cp -r $out/share/obs/obs-plugins/obs-face-tracker/obs-plugins/obs-face-tracker/* $out/share/obs/obs-plugins/obs-face-tracker/
        rm -rf $out/share/obs/obs-plugins/obs-face-tracker/obs-plugins
      fi
    '';
  };
in
{
  imports = [
    ./hardware-configuration.nix
    ../../modules/streamDeck.nix
  ];

  # ---------------------------------------------------------------------
  # Boot
  # ---------------------------------------------------------------------
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;
  
  boot.loader.systemd-boot.configurationLimit = 5;

  boot.initrd.kernelModules = [ 
    "nvidia" 
    "nvidia_modeset" 
    "nvidia_uvm" 
    "nvidia_drm" 
  ];

  boot.extraModulePackages = [
    config.boot.kernelPackages.v4l2loopback
  ];
  
  boot.kernelParams = [
    "nvidia_drm.modeset=1"
    "nvidia_drm.fbdev=1"
    "resume_offset=42432512"
  ];

  # Load the module on boot
  boot.kernelModules = [
    "v4l2loopback"
  ];

  # Optional: Module options to ensure compatibility with Chromium/WebRTC applications
  boot.extraModprobeConfig = ''
    options v4l2loopback devices=2 video_nr=10,11 card_label="DroidCam,OBS Virtual Camera" exclusive_caps=1,1
    blacklist i2c_nvidia_gpu
  '';

  # Ensure standard filesystem drivers are available if needed (e.g., ntfs, exfat)
  boot.supportedFilesystems = [ "ntfs" "exfat" "btrfs"];

  zramSwap = {
    enable = true;
    # Optional settings:
    algorithm = "zstd"; # Default is "zstd". Alternatives: "lz4", "lzo"
    memoryPercent = 50;  # Uses up to 50% of total RAM for zRAM (default is 50)
    priority = 100; # Higher priority: system uses zRAM FIRST
  };
  
  swapDevices = [ {
    device = "/swapfile";
    size = 36 * 1024; # Size in MB (16 GB). NixOS creates & formats this file automatically.
    priority = 1;     # Lower priority than zRAM (100)
  } ];

  # 2. Configure hibernation targets
  boot.resumeDevice = "/dev/disk/by-uuid/5a3bc9cb-cb7b-47d1-ad41-fd8d4e2bc6ac";

  # boot.loader.systemd-boot.edk2-uefi-shell.enable = true;

  # ---------------------------------------------------------------------
  # Networking
  # ---------------------------------------------------------------------
  networking.hostName = hostname;
  networking.networkmanager.enable = true;

  time.timeZone = "Europe/Warsaw";
  i18n.defaultLocale = "en_US.UTF-8";

  # ---------------------------------------------------------------------
  # Users
  # ---------------------------------------------------------------------
  users.users.${username} = {
    isNormalUser = true;
    description = username;
    extraGroups = [ "wheel" "networkmanager" "video" "audio" "input" "dialout" "uucp"];
    shell = pkgs.bash;
  };


  # ---------------------------------------------------------------------
  # niri (Wayland scrollable-tiling compositor)
  # ---------------------------------------------------------------------
  # This is the module shipped in nixpkgs itself (available on 26.05+),
  # so we don't need the third-party niri-flake. It pulls in the right
  # graphics/portal/session bits automatically.
  programs.niri.enable = true;

  # ---------------------------------------------------------------------
  # Login manager: greetd + tuigreet, launching a niri session
  # ---------------------------------------------------------------------
  services.greetd = {
    enable = true;
    settings = {
      default_session = {
        command = "${pkgs.tuigreet}/bin/tuigreet --time --remember --remember-session --asterisks --cmd niri-session";
        user = "greeter";
      };
    };
  };

  services.logind.settings.Login.HandlePowerKey = "poweroff";

  # ---------------------------------------------------------------------
  # Desktop plumbing niri needs (also recommended by the niri wiki)
  # ---------------------------------------------------------------------
  security.polkit.enable = true;
  services.gnome.gnome-keyring.enable = true;
  security.pam.services.greetd.enableGnomeKeyring = true;
  security.pam.services.swaylock = { };

  # NetworkManager applet / bluetooth / audio
  hardware.bluetooth.enable = true;
  services.blueman.enable = true;

  services.pipewire = {
    enable = true;
    alsa.enable = true;
    alsa.support32Bit = true;
    pulse.enable = true;
    wireplumber.enable = true;
  };

  security.rtkit.enable = true; # needed by pipewire

  # Power management (battery info, profiles - used by DMS's power widget)
  services.power-profiles-daemon.enable = true;
  services.upower.enable = true;

  # XDG portals for screen share / file pickers under Wayland
  xdg.portal = {
    enable = true;
    extraPortals = [ pkgs.xdg-desktop-portal-gtk ];
  };

  # ---------------------------------------------------------------------
  # NVIDIA (GTX 1660 / Turing, TU116)
  # ---------------------------------------------------------------------
  # Proprietary driver, not nouveau — needed for reliable Wayland support.

  hardware.graphics = {
    enable = true;
    enable32Bit = true; # Steam/Proton, 32-bit games
  };

  services.xserver.videoDrivers = [ "nvidia" ];

  hardware.nvidia = {
    modesetting.enable = true;      # required for Wayland
    powerManagement.enable = true; # set true only if you hit suspend/resume issues
    powerManagement.finegrained = false;
    open = false;                   # GTX 1660 (Turing/TU116) works with either;
                                     # closed module is the safer/better-tested default
    nvidiaSettings = true;
    package = config.boot.kernelPackages.nvidiaPackages.stable;
  };

  hardware.steam-hardware.enable = true;
  
  programs.steam = { # Global steam because fuck you, that's why
    enable = true;
    extraCompatPackages = with pkgs; [
      proton-ge-bin
    ];
    extest.enable = true;
    remotePlay.openFirewall = true; # Open ports for Steam Remote Play (optional)
    dedicatedServer.openFirewall = true; # Open ports for Source Dedicated Server (optional)
    localNetworkGameTransfers.openFirewall = true; # Open ports for local LAN downloads (optional)
  };

  programs.gamemode.enable = true;

  # ---------------------------------------------------------------------
  # Fonts (DMS uses Material Symbols + a normal UI font; add fallbacks)
  # ---------------------------------------------------------------------
  fonts.packages = with pkgs; [
    inter
    noto-fonts
    noto-fonts-color-emoji
    nerd-fonts.jetbrains-mono
    material-symbols
  ];
  fonts.fontconfig.defaultFonts = {
    sansSerif = [ "Inter" ];
    monospace = [ "JetBrainsMono Nerd Font" ];
  };

  # ---------------------------------------------------------------------
  # Misc system packages useful on any desktop
  # ---------------------------------------------------------------------
 
  environment.systemPackages = with pkgs; [
    fastfetch
    killall
    kitty                # terminal, launched from niri keybinds
    wl-clipboard
    grim
    slurp
    swappy              # screenshot editor DMS launches after captures
    brightnessctl
    playerctl
    xdg-utils
    xwayland-satellite  # lets X11-only apps run under niri (Wayland-native)
    vscode
    nvitop
    htop
    protonup-qt
    audacity
    kdePackages.gwenview
    kdePackages.kolourpaint
    kdePackages.ark
    bazaar
    p7zip         # Handles .7z, .zip, and basic extraction
    unrar         # Handles proprietary .rar files
    zip           # Creates .zip files
    unzip         # Extracts .zip files
    gzip          # Handles .tar.gz / .gz
    bzip2         # Handles .tar.bz2
    xz            # Handles .tar.xz
    zstd
    python314
    python314Packages.pip
    arduino-cli
    gcc
    clang              # Complements clang-tools
    cmake
    ninja              # Fast build tool used by CMake
    gnumake
    pkg-config         # Crucial for discovering libraries
    gdb                # Debugger
    clang-tools
    nirius
    yt-dlp
    ffmpeg
    git
    perl
    beammp-launcher
    zerotierone
    steam-run
    gamescope
    pavucontrol
    jdk25
    awww
    android-tools
    v4l-utils
    psmisc
    pulseaudio
    atuin
    ydotool
  ];

  
  services.flatpak.enable = true;

  # programs.bash.interactiveShellInit = ''
  #   eval "$(${pkgs.atuin}/bin/atuin init bash)"
  # '';

  programs.obs-studio = {
    enable = true;

    # Apply CUDA support to the underlying OBS package cleanly
    package = pkgs.obs-studio.override {
      cudaSupport = true;
    };

    # Let the module handle the wrapping for both standard and custom plugins
    plugins = [
      pkgs.obs-studio-plugins.obs-backgroundremoval
      pkgs.obs-studio-plugins.obs-source-clone
      pkgs.obs-studio-plugins.obs-recursion-effect
      pkgs.obs-studio-plugins.wlrobs
      pkgs.obs-studio-plugins.obs-dvd-screensaver
      
      # Your local let-bound derivation:
      obs-face-tracker
    ];
  };

  services.streamdeck-handler.enable = true;

  services.zerotierone = {
    enable = true;
    joinNetworks = [
      "633e31d8a270dc4a"
    ];
  };

  networking.firewall.allowedUDPPorts = [ 9993 ];

  networking.interfaces.enp2s0.ipv4.addresses = [ {
    address = "192.168.1.69";
    prefixLength = 24;
  } ];
  networking.defaultGateway = "192.168.1.254";
  networking.nameservers = [ "1.1.1.1" "8.8.8.8" ];

  programs.nix-ld = {
    enable = true;
    libraries = with pkgs; [
      stdenv.cc.cc
      zlib
      glibc
    ];
  };

  # Optional: Ensures <ESP32 USB flashing devices are recognized without root
  services.udev.packages = [ 
    pkgs.platformio-core
    pkgs.openocd
  ];

  services.udev.extraRules = ''
    KERNEL=="ttyUSB[0-9]*", MODE="0666", GROUP="dialout"
    KERNEL=="ttyACM[0-9]*", MODE="0666", GROUP="dialout"
  '';

  # Enable the udisks2 daemon
  services.udisks2.enable = true;

  nixpkgs.config.allowUnfree = true;

  # Ensure default MIME associations and XDG settings are generated
  xdg.mime.enable = true;
  xdg.menus.enable = true;

  # Provide the KDE applications menu definition Dolphin needs to index apps
  environment.etc."xdg/menus/applications.menu".text = 
  builtins.readFile "${pkgs.kdePackages.plasma-workspace}/etc/xdg/menus/plasma-applications.menu";

  environment.sessionVariables = {
    XDG_MENU_PREFIX = "plasma-";
    NIXOS_OZONE_WL = "1";
    WLR_NO_HARDWARE_CURSORS = "1";
    LIBVA_DRIVER_NAME = "nvidia";
    __GLX_VENDOR_LIBRARY_NAME = "nvidia";
  };

  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  system.stateVersion = "26.05";
}
