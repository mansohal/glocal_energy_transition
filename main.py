from gamspy import Container, Set, Parameter, Variable, Equation, Model, Sum, Sense
import numpy as np
import json
import sys
import os

# First test model: 20241106 FH first GAMSPy model
# See blend_example.py for another working GAMSPy example model

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # REPLACE THIS JSON BY JSON THAT MODEL RECEIVES WHEN LAUNCHED
    print(
        "Using as input_JSON the following. Please replace this with: input_JSON")
    input_JSON = {
        "cap": {
            "ror": 5,
            "gas": 5,
        }
    }

    # Check if dynamic input.json exists (for API usage)
    if os.path.exists("input.json"):
        try:
            with open("input.json", "r") as f:
                input_JSON = json.load(f)
        except json.JSONDecodeError:
            print("Invalid JSON in input.json; falling back to default values.", file=sys.stderr)

    dpy = 4 # Days per year simulated
    # print(" Mind might have to think about dpy again")
    upd = 12 # Time periods 'u' per day simulated (instead of 24 hours)

    # print("Note: For speed/simplicity in main data have a unique 'u' or always [d,u]?"
    #       "    Or another concept?"
    #       "    Maybe both, for treatments etc.: [d,u], but in Eqs simply s as segme"
    #       "     Or say [d,u] as day x mulit-hr, and then x as time-period?"
    #       "     Or then simpler to directly stick to [d,u] everywhere?")

    # Derived parameters
    hpu = 24 / upd
    nrep = 365 / dpy
    print(" Mind might have to think about nrep again")

    m = Container()

    # Set
    u = Set(m,"daytimes",
            records=[str(i) for i in range(upd)]
    )
    t = Set(m,"tech",
            records=['ror','gas']
    )

    # Par
    dem = Parameter(m,'dem',u,records=10*np.random.rand(len(u)))
    cap = Parameter(m,'cap',t,records=[["ror", input_JSON["cap"]["ror"]], ["gas", input_JSON["cap"]["gas"]]])
    # cap = Parameter(m,'cap',t,records=[["ror", 5], ["gas", 5]])
    vom = Parameter(m,'vom',t,records=[["ror", 10], ["gas", 100]])

    # Var
    gen = Variable(m,"gen", domain=[t,u], type='positive')
    gen.up[t,u] = cap[t]
    # pum = Variable(m,"gen", domain=[t,u], type='positive')
    costu = Variable(m, name="costu", domain=u, type="free")
    cost = Variable(m,"cost",type="free")

    # Eq
    mkl = Equation(m,'mkl',domain=u)
    mkl[u] = Sum(t, gen[t,u]) == dem[u]

    costu_ = Equation(m,'costu_',domain=u)
    costu_[u] = costu[u] == Sum(t, gen[t,u]*vom[t])

    cost_ = Equation(m,'cost_')
    cost_[...] = cost == nrep * hpu * Sum(u,costu[u])

    m1 = Model(
        container=m,
        name="m1",
        # equations=[mkl],
        # equations=[mkl,costu_],
        equations=[mkl,costu_,cost_],
        problem="LP",
        sense=Sense.MIN,
        objective= cost # Sum(alloy, price[alloy] * v[alloy]),
    )

    m1.solve()

    print(f"Meeting demand costs {cost.records.level[0]:.1f}")

    # SEND THIS JSON to user as model result:
    output_JSON = {
        "cost": cost.records.level[0]
    }

    #print("Writing output_JSON to command line. Please replace this with: Returning output_JSON to user client that launched the model run")
    #print(output_JSON)
    print(json.dumps(output_JSON))
    #print(json.dumps(output_JSON), file=sys.stdout)  # Ensure JSON goes to stdout

    # print("This is a debug message", file=sys.stderr)



    # report = Parameter(container=m, name="report", domain=[alloy, "*"])
    #
    # b1.solve()
    # report[alloy, "blend-1"] = v.l[alloy]
    #
    # b2.solve()
    # report[alloy, "blend-2"] = v.l[alloy]
    #
    # print("Look (hm, sometimes it doesn't show but if I run it manually just like that it works perfectly):")
    # report.pivot()
