{ config, pkgs, lib, inputs, username, ... }:

{
  imports = [
    ./dms-shell.nix
  ];

  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = "26.05";

  # -------------------------------------------------------------------
  # niri config file
  # -------------------------------------------------------------------
  # We're using the plain nixpkgs niri package (see system config), so
  # niri is configured the normal way: a KDL file at
  # $XDG_CONFIG_HOME/niri/config.kdl. Keeping it in a separate file
  # makes it easy to tweak (see home/niri/config.kdl).
  xdg.configFile."niri/config.kdl".source = ./niri/config.kdl;



  # -------------------------------------------------------------------
  # Session / GTK / Qt basics
  # -------------------------------------------------------------------
  gtk = {
    enable = true;
    theme = {
      name = "Adwaita-dark";
      package = pkgs.gnome-themes-extra;
    };
    iconTheme = {
      name = "Papirus-Dark";
      package = pkgs.papirus-icon-theme;
    };
  };

  qt = {
    enable = true;
    platformTheme.name = "gtk";
  };

  # -------------------------------------------------------------------
  # Everyday user packages
  # -------------------------------------------------------------------
  home.packages = with pkgs; [
    firefox
    chromium
    kdePackages.dolphin       # file manager (or swap for your favorite)
    mpv
    imv            # image viewer
    vlc
    vesktop
    droidcam
    jetbrains.clion
    cura-appimage
    qbittorrent
    prismlauncher
    
  ];

    programs.kitty = {
      enable = true;
      extraConfig = ''
        include dank-theme.conf
        include dank-tabs.conf
      '';
    };

    programs.firefox = {
      enable = true;
      profiles.dms-profile = {
        settings = {
          # 1. Force Firefox to load custom CSS
          "toolkit.legacyUserProfileCustomizations.stylesheets" = true;
        };

        # 2. Automatically generates ~/.mozilla/firefox/<profile>/chrome/userChrome.css
        userChrome = ''
          @import "file://${config.home.homeDirectory}/.config/dms/firefox/colors.css";
        '';
      };
    };
  
  home.pointerCursor = {
    gtk.enable = true;
    x11.enable = true;
    package = pkgs.bibata-cursors;
    name = "Bibata-Modern-Classic"; # Dark theme with smooth rounded corners
    size = 24;
  };

  home.sessionVariables = {
    NIXOS_OZONE_WL = "1";      # Electron/Chromium apps use Wayland
    MOZ_ENABLE_WAYLAND = "1";
  };

  services.udiskie.enable = true;

  programs.bash = {
  enable = true;
};

  programs.atuin = {
    enable = true;
    enableBashIntegration = true;
    
    # Turn off daemon mode to let the shell log commands directly to SQLite
    daemon.enable = false;

    settings = {
      auto_sync = true;
      sync_frequency = "15m";
      sync_address = "https://api.atuin.sh";
      search_mode = "fuzzy";
      style = "compact";
      enter_accept = false;
    };
  }; 

  programs.home-manager.enable = true;
}



