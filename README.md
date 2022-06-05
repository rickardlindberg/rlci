# RLCI

**An experimental CI/CD system designed to suit my needs.**

I have used [Jenkins](https://www.jenkins.io/) in many projects and I've had a
lot of success with it. However, over time I've also become more and more
frustrated with it, thinking that it is not the right tool for the job. It
feels like a patchwork of functionality that is difficult to get to work the
way I would like a CI/CD system to work.

## Vision

RLCI is an attempt to build a CI/CD system to suit my needs. What are my needs?
This is what I initially came up with:

* Ability to define flexible, **first-class pipelines**.
    * A pipeline defines a process. A change flows through a pipeline. (In
      Jenkins, a pipeline is run producing multiple pipeline runs.)
    * All steps should **run in isolation**. (In Jenkins, workspaces are
      reused, and one step can see the workspace used in another step.)
    * Pipelines should have a **visual representation**. (Jenkins can't show
      the whole pipeline until all steps have been run. If some steps at the
      end are run seldom, they will never be visualized.)
* Everything (pipelines/configuration/etc) is **written in code**. (In Jenkins,
  many things can be configured in the GUI which is a convenient way to start,
  but a pain in the long run.)
* Ability to re-rerun parts of a failed pipeline.

## Development

I will practice agile software development in this project. Some guiding
principles:

* **What is the simplest thing that could possible work?**
* **You ain't gonna need it! / Evolutionary design**
* **TDD / Refactoring**
* **Zero Friction Development**

### Stories

This is the backlog of stories to serve as a reminder of what might be
interesting to work on next.

* **Runs a hard-coded, pre-defined pipeline** Running pipelines is the core
  function of the CI/CD server. If we can get it to run a hard-coded,
  pre-defined pipeline, we have for sure demonstrated some progress.

* "My CI-server is a Linode. My pipeline is a Bash-script."
    * Linode provides same environment
    * Script provides process

### History

This is where I document the development. Links to completed stories and
videos.
