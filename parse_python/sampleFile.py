"""
A sample Python file demonstrating various language features and function interactions.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import math

@dataclass
class Point:
    x: float
    y: float

    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance to another point."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

def calculate_centroid(points: List[Point]) -> Optional[Point]:
    """Calculate the centroid of a list of points."""
    if not points:
        return None
    
    sum_x = sum(p.x for p in points)
    sum_y = sum(p.y for p in points)
    count = len(points)
    
    return Point(sum_x / count, sum_y / count)

def find_closest_point(target: Point, points: List[Point]) -> Optional[Point]:
    """Find the point closest to the target point."""
    if not points:
        return None
    
    return min(points, key=lambda p: target.distance_to(p))

def cluster_points(points: List[Point], num_clusters: int = 2) -> Dict[int, List[Point]]:
    """Group points into clusters using a simple algorithm."""
    if not points or num_clusters < 1:
        return {}
    
    # Initialize clusters with random points
    centroids = [points[i] for i in range(min(num_clusters, len(points)))]
    clusters: Dict[int, List[Point]] = {i: [] for i in range(len(centroids))}
    
    # Assign points to nearest centroid
    for point in points:
        closest_idx = min(range(len(centroids)), 
                         key=lambda i: point.distance_to(centroids[i]))
        clusters[closest_idx].append(point)
    
    return clusters

def main():
    # Create some sample points
    points = [
        Point(1.0, 2.0),
        Point(2.0, 3.0),
        Point(4.0, 5.0),
        Point(6.0, 7.0),
        Point(8.0, 9.0)
    ]
    
    # Find the centroid
    centroid = calculate_centroid(points)
    if centroid:
        print(f"Centroid: ({centroid.x:.2f}, {centroid.y:.2f})")
    
    # Find closest point to origin
    origin = Point(0.0, 0.0)
    closest = find_closest_point(origin, points)
    if closest:
        print(f"Closest point to origin: ({closest.x:.2f}, {closest.y:.2f})")
    
    # Cluster the points
    clusters = cluster_points(points, num_clusters=2)
    for cluster_id, points_in_cluster in clusters.items():
        print(f"\nCluster {cluster_id}:")
        for point in points_in_cluster:
            print(f"  Point: ({point.x:.2f}, {point.y:.2f})")

if __name__ == "__main__":
    main()
