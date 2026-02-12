# Tutorials

Welcome to the AAM tutorials! These hands-on guides walk you through real-world scenarios, from packaging your first project to advanced dependency management and multi-platform deployment.

## How to Use These Tutorials

Each tutorial is self-contained and can be completed independently. They range from beginner to advanced, with estimated completion times to help you plan your learning path.

All tutorials include:

- **Real-world scenarios** that solve practical problems
- **Step-by-step commands** with expected output
- **Full working examples** you can copy and paste
- **Clear explanations** of what's happening at each step

!!! tip "New to AAM?"
    Start with [Packaging Existing Skills](#packaging-existing-skills) to learn the basics, then move on to [Building a Code Review Package](#building-a-code-review-package) for a complete end-to-end workflow.

---

## Available Tutorials

<div class="grid cards" markdown>

-   :material-package-variant:{ .lg .middle } __Packaging Existing Skills__

    ---

    Learn how to use `aam pkg create` to bundle skills, agents, and instructions from an existing project.

    **Difficulty:** Beginner
    **Time:** 10 minutes

    [:octicons-arrow-right-24: Start tutorial](package-existing-skills.md)

-   :material-hammer-wrench:{ .lg .middle } __Building a Code Review Package__

    ---

    Build a complete security review toolkit from scratch with skills, agents, prompts, instructions, and tests.

    **Difficulty:** Intermediate
    **Time:** 25 minutes

    [:octicons-arrow-right-24: Start tutorial](build-code-review-package.md)

-   :material-share-variant:{ .lg .middle } __Sharing with Your Team__

    ---

    Set up local registries for team sharing via shared filesystems, Git repositories, or cloud storage.

    **Difficulty:** Beginner
    **Time:** 15 minutes

    [:octicons-arrow-right-24: Start tutorial](share-with-team.md)

-   :material-view-grid-plus:{ .lg .middle } __Multi-Platform Deployment__

    ---

    Configure simultaneous deployment to Cursor, Claude Desktop, and GitHub Copilot with a single install command.

    **Difficulty:** Intermediate
    **Time:** 15 minutes

    [:octicons-arrow-right-24: Start tutorial](multi-platform-deployment.md)

-   :material-graph:{ .lg .middle } __Working with Dependencies__

    ---

    Master dependency constraints, lock files, transitive dependencies, and conflict resolution.

    **Difficulty:** Intermediate
    **Time:** 20 minutes

    [:octicons-arrow-right-24: Start tutorial](working-with-dependencies.md)

</div>

---

## What You'll Need

Before starting the tutorials, make sure you have:

- **AAM installed** - See the [Installation Guide](../getting-started/installation.md)
- **Basic command line knowledge** - Familiarity with running terminal commands
- **A text editor** - For editing YAML and Markdown files

Some tutorials have additional prerequisites, which are listed at the start of each guide.

---

## After the Tutorials

Once you've completed these tutorials, you'll be ready to:

- Package your own skills and agents for distribution
- Set up a team registry for sharing artifacts
- Deploy packages across multiple AI platforms
- Manage complex dependency relationships
- Build production-ready agent packages

For deeper dives into specific topics, check out:

- [CLI Reference](../cli-reference/index.md) - Complete command documentation
- [Configuration Guide](../configuration/index.md) - Advanced configuration options
- [Platform Guides](../platforms/index.md) - Platform-specific deployment details
- [Advanced Topics](../advanced/index.md) - Security, governance, and custom registries

---

## Getting Help

If you run into issues while following these tutorials:

1. Check the [Troubleshooting Guide](../troubleshooting/index.md)
2. Run `aam doctor` to diagnose common problems
3. Review the relevant [CLI reference](../cli-reference/index.md) for command details
4. Ask in the [GitHub Discussions](https://github.com/aam-dev/aam/discussions)

Happy learning!
