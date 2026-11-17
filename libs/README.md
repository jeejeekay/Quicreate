# libs

Mod jars that Quicreate compiles against (compile only; the pack supplies the real mods at runtime).
They are not committed (see .gitignore). Put these five files here:

| File | Where it comes from |
|---|---|
| `create-1.20.1-6.0.8.jar` | the pack's `mods` folder |
| `create_mecanical_extruder-1.20.1-1.6.11-6.0.6.jar` | the pack's `mods` folder (the mod's own file name has the typo) |
| `flywheel-forge-1.20.1-1.0.5.jar` | inside the Create jar: `META-INF/jarjar/` |
| `Ponder-Forge-1.20.1-1.0.91.jar` | inside the Create jar: `META-INF/jarjar/` |
| `Registrate-MC1.20-1.3.3.jar` | inside the Create jar: `META-INF/jarjar/` |

When the pack updates Create or the extruder, replace the jars and change the versions in `gradle.properties`.
