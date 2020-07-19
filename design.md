## Overall

```
Yaml  ---> yaml.load ---> |                                                           | ---> SVG
                          | ---> Normalizer ---> Resolver ---> Renderer ---> SVG ---> |
Sch   ---> Parser ------> |                                                           | ---> PNG
```

## Resolver
It's complecated, it should be refactored.

* Dict to Class Object
* Resolve Dependencies between the schedules (task or milestone)
  - generate paths (edged)
