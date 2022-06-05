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

* **Extend hard coded pipeline to integrate a branch** The hard coded pipeline
  currently does nothing. We could start fleshing out this pipeline to be the
  pipeline that RLCI could use. The first step in that pipeline should be to
  integrate a branch (merge with `main` and run tests and promote if passed).

* **More realistic output** The pipeline currently writes its "report" to
  stdout. I imagine the CI-server having a web-front end to display its status.
  Therefor convert the stdout report to a HTLM-file that can be served by a web
  server.

* **More realistic environment** One purpose of a CI server is to provide the
  same environment for integration builds. That requires the CI server to not
  run on my laptop. Create a dedicated server to which RLCI can be deployed and
  run. (My CI-server is a Linode. My pipeline is the RLCI program. Linode
  provides same environment / integration point.  RLCI provides process.)

### History

This is where I document the completed stories development.

#### #1 Runs a hard-coded, pre-defined pipeline

*Running pipelines is the core function of the CI/CD server. If we can get it
to run a hard-coded, pre-defined pipeline, we have for sure demonstrated some
progress.*

I completed the main part of this story in a video. Watch me get all the
infrastructure in place to write a test for the very first version of RLCI:

    TODO: link video once it is edited

Browse the
[code](https://github.com/rickardlindberg/rlci/tree/w23-rlci-reboot-end) as it
looked like at the end of the video and look at the complete
[diff](https://github.com/rickardlindberg/rlci/compare/d3bda99f9d427865f9f1c2e394a5c7c392bcdc12...453ae3d26e70a2af1577ee4a06ae2001c8038606)
of changes.

After the video I did some
[refactorings](https://github.com/rickardlindberg/rlci/compare/e1c4c5c34b75856ca8e62ad172045778a3af8f63...d5bd857e66682ebdc5ad136d7b8270d7e3915961)
and made some more improvements to the build system:

* [Usage should exit with code 1.](https://github.com/rickardlindberg/rlci/commit/48a6c55fc2356718c49a080500ba81bf1c78ba88)
* [Exit with code 0 if tests fail.](https://github.com/rickardlindberg/rlci/commit/03a8a53e218f3c0de81be3e47d79b93f46428a57) (Should have been "code 1" in message.)
* [Update usage and inluce the build command.](https://github.com/rickardlindberg/rlci/commit/b39d5a5cffd359365223d591558d38fafc81ac30)
