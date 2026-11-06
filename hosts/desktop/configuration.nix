{ config, pkgs, username, ... }:

let
  #qemuFresh = import ../../pkgs/qemu-fresh.nix { inherit pkgs; }; 
in
{
  imports = [
    ./hardware-configuration.nix

    # shared by every machine
    ../../modules/common/base.nix
    ../../modules/common/packages.nix
    ../../modules/common/zerotier.nix

    # desktop-specific
    ../../modules/desktop/boot.nix
    ../../modules/desktop/nvidia.nix
    ../../modules/desktop/desktop.nix
    ../../modules/desktop/gaming.nix
    #../../modules/desktop/obs.nix
    ../../modules/desktop/networking.nix
    ../../modules/desktop/streamDeck.nix
    ../../modules/desktop/waydroid.nix
    ../../modules/desktop/audio-share.nix
    ../../modules/desktop/nix-store.nix
  ];

  users.users.${username} = {
    isNormalUser = true;
    description = username;
    extraGroups = [ "wheel" "networkmanager" "video" "audio" "input" "dialout" "uucp" "i2c" "render" "adbusers" "libvirtd" "kvm" ];
    shell = pkgs.bash;
  };

  environment.systemPackages = with pkgs; [
    kitty
    wl-clipboard
    grim
    slurp
    swappy
    brightnessctl
    playerctl
    xdg-utils
    xwayland-satellite
    #vscode
    vscodium
    nvitop
    protonup-qt
    audacity
    kdePackages.gwenview
    kdePackages.kolourpaint
    kdePackages.ark
    bazaar
    unrar
    python314
    python314Packages.pip
    arduino-cli
    gcc
    clang
    cmake
    ninja
    gnumake
    pkg-config
    gdb
    clang-tools
    nirius
    yt-dlp
    ffmpeg
    perl
    beammp-launcher
    steam-run
    gamescope
    pavucontrol
    jdk25
    awww
    android-tools
    v4l-utils
    pulseaudio
    ydotool
    ddcutil
    xwayland
    parted
    xorriso
    nodejs_26
    vulkan-tools
    mesa-demos
    #qemuFresh # remember to update later when nixpkgs catches up
    piper
    rivalcfg
    kdePackages.kdeconnect-kde
    scrcpy
    r2modman
    dotnet-sdk_10
    # gnome-boxes
    
  ];

  fonts.packages = [ pkgs.noto-fonts-cjk-sans ];

  # programs.virt-manager.enable = true;

  # virtualisation.spiceUSBRedirection.enable = true;
  # virtualisation.libvirtd = {
  #   enable = true;
  # };

  nixpkgs.config.permittedInsecurePackages = [
    "ventoy-1.1.12"
  ];

  services.flatpak.enable = true;

  programs.appimage.enable = true;
  programs.appimage.binfmt = true;

  services.streamdeck-handler.enable = true;

  programs.nix-ld = {
    enable = true;
    libraries = with pkgs; [
      stdenv.cc.cc
      zlib
      glibc
    ];
  };

  services.udev.packages = [ 
    pkgs.platformio-core
    pkgs.openocd
    pkgs.rivalcfg
  ];

  services.udev.extraRules = ''
    KERNEL=="ttyUSB[0-9]*", MODE="0666", GROUP="dialout"
    KERNEL=="ttyACM[0-9]*", MODE="0666", GROUP="dialout"
    
    SUBSYSTEM=="usb", ATTR{idVendor}=="1038", MODE="0666"
  '';

  services.udisks2.enable = true;

  nixpkgs.config.android_sdk.accept_license = true;

  services.pipewire = {
    enable = true;
    alsa.enable = true;
    alsa.support32Bit = true;
    pulse.enable = true;
  };


  xdg.portal = {
    enable = true;
    wlr.enable = true;
    extraPortals = [ 
      pkgs.xdg-desktop-portal-gnome
      pkgs.xdg-desktop-portal-gtk 
    ];
    config.common.default = "*";
  };

  services.ratbagd.enable = true;

  services.tardbot = {
    enable = true; #[cite: 5]
    environmentFile = "/etc/tardbot.env"; # Path to file containing DISCORD_TOKEN=...[cite: 5]
    modules = [ "music" "general" "r34" "vcmanager" ];     # Optional: specific modules to load[cite: 5]
    
    # Optional extra settings / environment variables
    settings = {
      INTERLEAVE_MODE = "spread";
      YTDLP_CLIENTS = "visionos";
      TEMP_VC_CATEGORY_ID = "1454932444825260262";
      VC_COMMAND_COOLDOWN = "10";
    };
  };

  services.audio-share.enable = true;


  system.stateVersion = "26.05";
}