# aigonskills

A collection of Claude Code skills.

## Skills

| Skill | Description |
|-------|-------------|
| [simplify](skills/examples/simplify/) | Clean up recently changed code — removes complexity, extracts duplication |
| [review](skills/examples/review/) | Review branch or staged changes for bugs, security issues, and style |
| [init](skills/examples/init/) | Generate a `CLAUDE.md` for a project |
| [fourier](skills/examples/fourier/) | FFT spectrum analysis — plots frequency content from CSV, WAV, or demo signal |

## Usage

Copy any skill directory into `.claude/skills/` in your project, or `~/.claude/skills/` for global use. Then invoke with `/skill-name`.

## Structure

```
skills/
└── skill-name/
    └── SKILL.md
```

## License

MIT
