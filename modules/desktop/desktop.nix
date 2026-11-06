{ pkgs, ... }:

{
  programs.niri.enable = true;

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

  security.polkit.enable = true;
  services.gnome.gnome-keyring.enable = true;
  security.pam.services.greetd.enableGnomeKeyring = true;
  security.pam.services.swaylock = { };

  hardware.bluetooth.enable = true;
  services.blueman.enable = true;

  services.pipewire = {
    enable = true;
    alsa.enable = true;
    alsa.support32Bit = true;
    pulse.enable = true;
    wireplumber.enable = true;
  };

  security.rtkit.enable = true;

  services.power-profiles-daemon.enable = true;
  services.upower.enable = true;

  xdg.portal = {
    enable = true;
    extraPortals = [ pkgs.xdg-desktop-portal-gtk ];
  };

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

  xdg.mime.enable = true;
  xdg.menus.enable = true;
  environment.etc."xdg/menus/applications.menu".text = 
    builtins.readFile "${pkgs.kdePackages.plasma-workspace}/etc/xdg/menus/plasma-applications.menu";

  environment.sessionVariables.XDG_MENU_PREFIX = "plasma-";
}