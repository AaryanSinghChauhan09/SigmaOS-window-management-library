    # SigmaOS-window-management-library

    Compositor / window-manager library

    Part of the **SigmaOS** sovereign operating-system ecosystem — a multi-repository
    distribution modelled on Linux Mint and Omarchy Linux. See the parent
    [`SigmaOS`](https://github.com/AaryanSinghChauhan09/SigmaOS) repository for the
    full component index.

    ## Upstream inspirations
    - https://github.com/linuxmint/muffin
- https://github.com/omacom/omarchy-hyprland-titlebars

    ## Design principles applied
    - **Declarative Configuration**
- **Separation of Concerns**
- **Defensive Programming**
- **Fail-Fast**
- **KISS**
- **Deterministic Testing**

    ## Usage
    Verbs: `rules, decorations, workspaces, apply-plan`

    ```
    $ sigma-wm rules --add --class Firefox --workspace 2
$ sigma-wm rules --list
$ sigma-wm decorations --buttons menu:minimize:close --border 6
$ sigma-wm workspaces --window "class=Firefox,title=.*Mozilla"
$ sigma-wm apply-plan --window "class=Firefox,title=.*Mozilla"   # prints plan (dry-run)

    ```

    ## Build & test
    ```
    make build
    make test
    ```

    ## Licence
    GNU General Public License v3.0 (FOSS).
