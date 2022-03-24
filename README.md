An experimental CI/CD system designed to solve problems I've had with Jenkins.

## TODO

* Flesh out stage input/output
    * Write simple realistic pipeline
    * shell [name] "...."
    * out name "${...}"
    * **Compile stage to Python script**
    * `./tools.py run_stage [stage name] arg1=foo arg2=bar`
    * `echo [stage ast] | ./tools.py run arg1=foo arg2=bar`
        * Streaming json lines
            ["Log" "out" "..."]
            ["Log" "err" "..."]
            ["Result" {...}]
        * Formatted nicely if run from console
* Allow template for stage body
    * Store two kinds of templates: block | stageBody
* Add concept of a pipeline with a title?
* What should introduce a new scope? global/pipeline/template
* RLMeta
    * Syntax to capture location -> function that raises error at that location
