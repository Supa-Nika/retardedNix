{
  description = "NixOS desktop: niri + DankMaterialShell (DMS)";

  inputs = {
    # niri (native nixpkgs module) needs a fairly recent nixpkgs.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

    home-manager = {
      url = "github:nix-community/home-manager/release-26.05";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # DankMaterialShell itself
    dms = {
      url = "github:AvengeMedia/DankMaterialShell/stable";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # dgop powers DMS's system-monitor widgets; pulling it from the flake
    # gets you faster updates than whatever ships in nixpkgs.
    dgop = {
      url = "github:AvengeMedia/dgop";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    tardbot.url = "github:Supa-Nika/MusicBotThingy";

    rivalcfg-src = {
      url = "github:flozz/rivalcfg";
      flake = false;
    };

  };

  # TUTAJ DODAJ musicbot-repo do listy argumentów outputs:
  outputs = { self, nixpkgs, home-manager, dms, dgop, tardbot, rivalcfg-src, ... }@inputs:
    let
      system = "x86_64-linux";

      # ----------------------------------------------------------------
      # Edit these two to match your machine / account.
      # ----------------------------------------------------------------
      hostname = "radzieckaMaszyna";
      username = "mieciu";
      
      serverHostname = "radzieckaMaszyna2";
    in
    {
      nixosConfigurations.${hostname} = nixpkgs.lib.nixosSystem {
        inherit system;
        specialArgs = { inherit inputs username hostname; };
        modules = [
          ./hosts/desktop/configuration.nix

          ({ pkgs, ... }: {
            environment.systemPackages = [
              (pkgs.python3Packages.buildPythonApplication {
                pname = "rivalcfg";
                version = "git";
                src = rivalcfg-src;
                pyproject = true;
                build-system = [ pkgs.python3Packages.flit-core ];
                dependencies = [ pkgs.python3Packages.hidapi ];
                doCheck = false;
              })
            ];

            services.udev.extraRules = ''
              SUBSYSTEM=="usb", ATTRS{idVendor}=="1038", TAG+="uaccess"
              KERNEL=="hidraw*", ATTRS{idVendor}=="1038", TAG+="uaccess"
            '';
          })

          home-manager.nixosModules.home-manager
          {
            home-manager.useGlobalPkgs = true;
            home-manager.useUserPackages = true;
            home-manager.extraSpecialArgs = { inherit inputs username; };
            home-manager.users.${username} = import ./home/home.nix;
            home-manager.backupFileExtension = "hm-bak";
          }
        ];
      };

      # Headless server (BIOS/GRUB, SATA disk). No desktop or GPU; home-manager is just atuin.
      nixosConfigurations.${serverHostname} = nixpkgs.lib.nixosSystem {
        inherit system;
        specialArgs = { inherit inputs username; hostname = serverHostname; };
        modules = [
          ./hosts/server/configuration.nix

          home-manager.nixosModules.home-manager
          {
            home-manager.useGlobalPkgs = true;
            home-manager.useUserPackages = true;
            home-manager.extraSpecialArgs = { inherit inputs username; };
            home-manager.users.${username} = import ./home/server.nix;
            home-manager.backupFileExtension = "hm-bak";
          }

          tardbot.nixosModules.default

        ];
      };

      nixosConfigurations.waydroid-vm = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [ ./hosts/waydroid-vm/configuration.nix ];
      };
    };
}