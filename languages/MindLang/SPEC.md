# MindLang Specification

## Purpose

MindLang is a declarative language for specifying artificial cognitive organisms. It compiles to a Mind Genome which can be instantiated as a running organism.

## Syntax (Planned)

```
organism Navigator {
    sense: [vision(spatial[224,224,3]), lidar(spatial[360,1])]
    
    memory {
        episodic(decay=exponential, capacity=10000)
        semantic(decay=power_law)
        procedural(decay=slow)
        working(capacity=7)
        counterfactual(decay=fast)
    }
    
    values {
        constraint: no_self_harm
        constraint: human_override
        goal: navigate_safely(priority=0.9)
        goal: minimize_energy(priority=0.6)
        preference: prefer_known_routes(weight=0.3)
    }
    
    drives {
        curiosity(weight=0.7, trigger=uncertainty>0.5)
        efficiency(weight=0.5, trigger=energy<0.3)
    }
    
    safety {
        max_risk: MEDIUM
        audit: all
        immutable: [no_self_harm, human_override]
    }
    
    development {
        stage: embryonic → nascent at confidence>0.5
        stage: nascent → developing at prediction_error<0.3
    }
}
```

## Compilation Pipeline

MindLang → AST → Genome YAML → Organism Instance

## Status

Planned for v0.4.0.
