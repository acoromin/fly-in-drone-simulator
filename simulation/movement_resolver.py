from graph import Hub, Connection


class MovementResolver:
    def __init__(self, graph: dict[Hub, list[Connection]]) -> None:
        self.graph = graph

    def get_connection(
            self,
            current_hub: Hub,
            next_hub: Hub) -> Connection | None:
        for connection in self.graph[current_hub]:
            if (
                connection.source == current_hub
                and connection.target == next_hub
            ) or (
                connection.target == current_hub
                and connection.source == next_hub
            ):
                return connection
        return None

    def get_hub_occupancy(self, proposals: list[dict]) -> dict[Hub, int]:
        occupancy = {}
        for proposal in proposals:
            hub = proposal["current"]
            if hub not in occupancy:
                occupancy[hub] = 1
            else:
                occupancy[hub] += 1
        return occupancy

                

    def filter_link_capacity(self, proposals: list[dict]) -> list[dict]:
        valid_proposals = []
        link_usage = {}
        for proposal in proposals:
            current_hub = proposal["current"]
            next_hub = proposal["next"]

            connection = self.get_connection(current_hub, next_hub)
            if connection in link_usage:
                link_usage[connection] += 1
            else:
                link_usage[connection] = 1
            if link_usage[connection] <= connection.max_link_capacity:
                valid_proposals.append(proposal)

        return valid_proposals

    def filter_hub_capacity(
            self,
            proposals: list[dict],
            occupancy: dict[Hub, int]
            ) -> list[dict]:




 

    def resolve_proposals(self, proposals: list[dict]) -> list[dict]:
        filtered_links = self.filter_link_capacity(proposals)

