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

## Notes

### Where should a pipeline be defined?

Jenkins and other CI/CD systems make us define the pipeline in the repo itself.
Does that make sense?

On the one hand, it ensures that the pipeline is always in sync with the repo.
If a build command changes, we can update the pipeline build step accordingly.

On the other hand, it doesn't feel right that the repo has knowledge of where
it is deployed for example.

A pipeline encodes a process for software delivery. The process and the code
can change independently.

**If things change together, they should be together. If not, they should
not.**

My current thinking is that the repo should expose an interface to the pipeline
for doing certain tasks. For example `./zero.py build` to build and test, and
`./zero.py deploy` to deploy the application somewhere. If the build
process changes, only a change to `zero.py` is needed, and the pipeline can
stay the same.

## Development

I will practice agile software development in this project. Some guiding
principles:

* **What is the simplest thing that could possibly work?**
* **You ain't gonna need it! / Evolutionary design**
* **TDD / Refactoring**
* **Zero Friction Development**

### Stories

This is the backlog of stories to serve as a reminder of what might be
interesting to work on next.

* **Custom pipelines** There is only one hard coded pipeline. Make it possible
  to define more and trigger them from the CLI.

* **More realistic output** The pipeline currently writes its "report" to
  stdout. I imagine the CI-server having a web-front end to display its status.
  Therefore convert the stdout report to a HTLM-file that can be served by a
  web server.

* **More realistic environment** One purpose of a CI server is to provide the
  same environment for integration builds. That requires the CI server to not
  run on my laptop. Create a dedicated server to which RLCI can be deployed and
  run. (My CI-server is a Linode. My pipeline is the RLCI program. Linode
  provides same environment / integration point.  RLCI provides process.)

### History

This is where I document the completed stories.

#### #1 Runs a hard-coded, pre-defined pipeline

*Running pipelines is the core function of the CI/CD server. If we can get it
to run a hard-coded, pre-defined pipeline, we have for sure demonstrated some
progress.*

I completed the main part of this story in a video. Watch me get all the
infrastructure in place to write a test for the very first version of RLCI.

**VIDEO:** [Rebooting RLCI with an agile approach using TDD and zero friction
development.](https://youtu.be/Re7litDdulU)

Browse the
[code](https://github.com/rickardlindberg/rlci/tree/w23-rlci-reboot-end) as it
looked like at the end of the video and look at the complete
[diff](https://github.com/rickardlindberg/rlci/compare/d3bda99f9d427865f9f1c2e394a5c7c392bcdc12...453ae3d26e70a2af1577ee4a06ae2001c8038606)
of changes.

After the video I did some
[refactoring](https://github.com/rickardlindberg/rlci/compare/e1c4c5c34b75856ca8e62ad172045778a3af8f63...d5bd857e66682ebdc5ad136d7b8270d7e3915961)
and made some more improvements to the build system:

* [Usage should exit with code 1.](https://github.com/rickardlindberg/rlci/commit/48a6c55fc2356718c49a080500ba81bf1c78ba88)
* [Exit with code 0 if tests fail.](https://github.com/rickardlindberg/rlci/commit/03a8a53e218f3c0de81be3e47d79b93f46428a57) (Should have been "code 1" in message.)
* [Update usage and inluce the build command.](https://github.com/rickardlindberg/rlci/commit/b39d5a5cffd359365223d591558d38fafc81ac30)

#### #2 Extend hard coded pipeline to integrate a branch

*The hard coded pipeline currently does nothing. We could start fleshing out
this pipeline to be the pipeline that RLCI could use. The first step in that
pipeline should be to integrate a branch (merge with `main` and run tests and
promote if passed).*

I completed this story along with some clean up in a video.

**VIDEO:** [Adding continuous integration functionality to
RLCI.](https://youtu.be/sokSvnAkd5E)

Browse the
[code](https://github.com/rickardlindberg/rlci/tree/w24-extend-hard-coded-pipeline)
as it looked like at the end of the video and look at the complete
[diff](https://github.com/rickardlindberg/rlci/compare/745a36ef6e3ede7cf8b6b6643058a0baeb570d2d...w24-extend-hard-coded-pipeline)
of changes.

#### #3 Extend hard coded pipeline to run in isolation

*This prevents multiple pipeline runs to interfere with each other via
contaminated workspaces.*

I completed this story in a video. Watch me do refactoring, internal
improvements, and finally adding functionality to execute pipelines in
isolation.

**VIDEO:** [Making RLCI pipelines run in
isolation.](https://youtu.be/0jJEPgomRCc)

Browse the
[code](https://github.com/rickardlindberg/rlci/tree/w25-pipeline-run-in-isolation)
as it looked like at the end of the video and look at the complete
[diff](https://github.com/rickardlindberg/rlci/compare/86e4bf72c35c4fb035fcc5caa58218684ccc06b4...w25-pipeline-run-in-isolation)
of changes.

##### Retro

I am not happy with how the design turned out. I'm not sure it will allow me to
move forward smoothly. I think I will spend some time researching
testing/design strategies applicable for me in this situation.

But can I do that without also working on a story?

I think adding more realistic output will require that I have a better design.
So perhaps I should try to refactor towards a design that will make reporting
easy to implement. And then implement that.

Overall, I think that much time needs to be spend on refactoring/design.
Perhaps this ratio is higher in the beginning of a project. I feel like 90/10
design/refactoring vs. implementing stories.

#### #4 Make pipeline print to the terminal what it is doing

This story started out with a bunch of refactoring and design. I wasn't really
sure what story to work on when I started. I just knew I needed to clean up
some things before I could move on. Once I was happier with the design, it was
quite natural to extend the pipeline to report what it was doing, so that's
what I did.

##### Retro

* The article [Favor real dependencies for unit
  testing](https://stackoverflow.blog/2022/01/03/favor-real-dependencies-for-unit-testing/)
  presented a solution to a design problem I was having. (For more info, see
  the upcoming video.

* Functional core, imperative shell. Hexagonal architecture. A-frame
  architecture. They are all similar. Thinking in terms of pure/IO Haskell
  functions made it pretty clear to me. I feel like RLCI is quite free from
  pure logic at this point. It is mostly stitching together infrastructure
  code. But I will keep it in mind and look for opportunities to extract pure
  functions.

* Evolutionary design is hard. What if the first step was in the wrong
  direction? At least a rewrite is not a rewrite of that much.

* I used the TDD principle of taking every shortcut possible to get a test
  passing, and then improved the design with refactoring. (When writing the new
  infrastructure wrapper `Process`.) It felt awkward to do ugly things, but I
  got to a clean solution faster.

* I caught myself having done some premature parametrization and [removed
  it](https://github.com/rickardlindberg/rlci/commit/185f184f0f1f477f5818bfa44e8803bc71dc727e).
