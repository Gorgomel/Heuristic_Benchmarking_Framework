def test_hpc_framework_cli_main(capsys):
    from hpc_framework.cli import main

    main()
    assert "alive" in capsys.readouterr().out.lower()


def test_greedy_runs_small_graph():
    import networkx as nx

    from heuristics.greedy import run_greedy_heuristic

    G = nx.path_graph(6)
    run_greedy_heuristic(G, delta_v=0.1)  # smoke


def test_orchestrator_import_only():
    import orchestrator.ssh_executor as m

    assert hasattr(m, "execute_remote_experiment")
