import time

from helpers import setup_deployment, cleanup_deployment, query_dep, adjust_dep


def test_query_settings_cpu():
    dep = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: test-query-settings-cpu
    spec:
      selector:
        matchLabels:
          app: test-query-settings-cpu
      template:
        metadata:
          labels:
            app: test-query-settings-cpu
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              resources:
                limits:
                  cpu: .3
    """
    cfg = """
    k8s:
      application:
        components:
          test-query-settings-cpu:
            settings:
              cpu:
                min: .1
                max: .5
                step: .1
    """
    setup_deployment(dep)
    desc = query_dep(cfg)
    assert desc['application']['components']['test-query-settings-cpu']['settings']['cpu']['value'] == .3
    cleanup_deployment(dep)


def test_query_settings_mem():
    dep = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: test-query-settings-mem
    spec:
      selector:
        matchLabels:
          app: test-query-settings-mem
      template:
        metadata:
          labels:
            app: test-query-settings-mem
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              resources:
                limits:
                  memory: .25Gi
    """
    cfg = """
    k8s:
      application:
        components:
          test-query-settings-mem:
            settings:
              mem:
                min: .1
                max: .5
                step: .1
    """
    setup_deployment(dep)
    desc = query_dep(cfg)
    assert desc['application']['components']['test-query-settings-mem']['settings']['mem']['value'] == .25
    cleanup_deployment(dep)


def test_query_settings_replicas():
    dep = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: test-query-settings-replicas
    spec:
      replicas: 2
      selector:
        matchLabels:
          app: test-query-settings-replicas
      template:
        metadata:
          labels:
            app: test-query-settings-replicas
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
    """
    cfg = """
    k8s:
      application:
        components:
          test-query-settings-replicas:
            settings:
              replicas:
                min: 1
                max: 2
                step: 1
    """
    setup_deployment(dep)
    desc = query_dep(cfg)
    assert desc['application']['components']['test-query-settings-replicas']['settings']['replicas']['value'] == 2
    cleanup_deployment(dep)


def test_adjust_settings_cpu():
    dep = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: test-adjust-settings-cpu
    spec:
      selector:
        matchLabels:
          app: test-adjust-settings-cpu
      template:
        metadata:
          labels:
            app: test-adjust-settings-cpu
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              resources:
                limits:
                  cpu: .3
    """
    cfg = """
    k8s:
      application:
        components:
          test-adjust-settings-cpu:
            settings:
              cpu:
                min: .1
                max: .5
                step: .1
    """
    setup_deployment(dep)
    adjust_dep(cfg, {'application': {'components': {'test-adjust-settings-cpu': {'settings': {'cpu': {'value': .2}}}}}})
    desc = query_dep(cfg)
    assert desc['application']['components']['test-adjust-settings-cpu']['settings']['cpu']['value'] == .2
    cleanup_deployment(dep)


def test_adjust_settings_mem():
    dep = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: test-adjust-settings-mem
    spec:
      selector:
        matchLabels:
          app: test-adjust-settings-mem
      template:
        metadata:
          labels:
            app: test-adjust-settings-mem
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              resources:
                limits:
                  memory: .25Gi
    """
    cfg = """
    k8s:
      application:
        components:
          test-adjust-settings-mem:
            settings:
              mem:
                min: .1
                max: .5
                step: .1
    """
    setup_deployment(dep)
    adjust_dep(cfg,
               {'application': {'components': {'test-adjust-settings-mem': {'settings': {'mem': {'value': .125}}}}}})
    desc = query_dep(cfg)
    assert desc['application']['components']['test-adjust-settings-mem']['settings']['mem']['value'] == .125
    cleanup_deployment(dep)


def test_adjust_settings_replicas():
    dep = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: test-adjust-settings-replicas
    spec:
      replicas: 2
      selector:
        matchLabels:
          app: test-adjust-settings-replicas
      template:
        metadata:
          labels:
            app: test-adjust-settings-replicas
        spec:
          containers:
          - name: main
            image: alpine:latest
            command: ["/bin/sh", "-c", "sleep 3600"]
    """
    cfg = """
    k8s:
      application:
        components:
          test-adjust-settings-replicas:
            settings:
              replicas:
                min: 1
                max: 2
                step: 1
    """
    setup_deployment(dep)
    adjust_dep(cfg,
               {'application': {
                   'components': {'test-adjust-settings-replicas': {'settings': {'replicas': {'value': 1}}}}}})
    desc = query_dep(cfg)
    assert desc['application']['components']['test-adjust-settings-replicas']['settings']['replicas']['value'] == 1
    cleanup_deployment(dep)
