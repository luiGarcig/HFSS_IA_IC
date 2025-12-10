import numpy as np
from collections import deque
from typing import List, Tuple, Deque, Optional, Union

Matrix = List[List[int]]
Coord = Tuple[int, int]
PredecessorMap = List[List[Optional[Coord]]]

def verify_path(
    matrix: Matrix,
    start_pos: Tuple[int, int],
    end_pos: Tuple[int, int]
    ) -> bool:

    R = len(matrix) #-> row  
    C = len(matrix[0]) #-> column

    start_r, start_c = start_pos
    end_r, end_c = end_pos

    if start_pos == end_pos:
        return True
    
    queue: Deque[Tuple[int, int]] = deque([start_pos])
    
    visited = set([start_pos])
    
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    while queue:
        r, c = queue.popleft()

        for dr, dc in directions:
            nr, nc = r + dr, c + dc 

            if 0 <= nr < R and 0 <= nc < C:
                
                if (nr, nc) == end_pos:
                    return True
                
                if matrix[nr][nc] == 1 and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))

    return False


def create_path_matrix(
    matrix_size: int,
    start: List[int],
    end: List[int],
) -> Union[Matrix, str]:

    start_tuple: Coord = tuple(start)
    end_tuple: Coord = tuple(end)
    
    PROXIMITY_LIMIT = 1

    matrix: Matrix = [[0] * matrix_size for _ in range(matrix_size)]
    
    queue = deque([start_tuple]) 
    visited: List[List[bool]] = [[False] * matrix_size for _ in range(matrix_size)]
    visited[start[0]][start[1]] = True  
    predecessor: PredecessorMap = [[None] * matrix_size for _ in range(matrix_size)]

    direction_y = [-1, 1, 0, 0] 
    direction_x = [0, 0, -1, 1]

    path_found = False
    
    # Função auxiliar para "Distância de Manhattan" (passos em L)
    def manhattan_distance(p1: Coord, p2: Coord) -> int:
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    while queue:
        current_row, current_col = queue.popleft()
        current_tuple: Coord = (current_row, current_col)

        if current_tuple == end_tuple:
            path_found = True
            break 

        for i in range(4):
            next_row = current_row + direction_y[i]
            next_col = current_col + direction_x[i]
            next_tuple: Coord = (next_row, next_col)

            # 1. Verifica se está dentro dos limites
            is_in_bounds = (0 <= next_row < matrix_size) and \
                           (0 <= next_col < matrix_size)
            if not is_in_bounds:
                continue

            # 2. Verifica se já foi visitado
            if visited[next_row][next_col]:
                continue
            
            # 3. Verifica se a *próxima* célula é uma borda
            is_next_a_border = (next_row == 0 or next_row == matrix_size - 1 or
                                next_col == 0 or next_col == matrix_size - 1)

            # --- LÓGICA DE PROXIMIDADE ---
            
            # Regra 1: O movimento é livre se NÃO for uma borda
            if not is_next_a_border:
                visited[next_row][next_col] = True
                predecessor[next_row][next_col] = current_tuple
                queue.append(next_tuple)
                continue # Movimento permitido, checar próximo vizinho

            # Se chegamos aqui, is_next_a_border é True.
            # Agora checamos as exceções.

            # Regra 2: Permitido se for o ponto final
            if next_tuple == end_tuple:
                visited[next_row][next_col] = True
                predecessor[next_row][next_col] = current_tuple
                queue.append(next_tuple)
                continue

            # Regra 3: Permitido se o PONTO ATUAL estiver perto do INÍCIO
            is_near_start = manhattan_distance(current_tuple, start_tuple) <= PROXIMITY_LIMIT
            if is_near_start:
                visited[next_row][next_col] = True
                predecessor[next_row][next_col] = current_tuple
                queue.append(next_tuple)
                continue
                
            # Regra 4: Permitido se o PRÓXIMO PONTO estiver perto do FIM
            is_near_end = manhattan_distance(next_tuple, end_tuple) <= PROXIMITY_LIMIT
            if is_near_end:
                visited[next_row][next_col] = True
                predecessor[next_row][next_col] = current_tuple
                queue.append(next_tuple)
                continue
            
            # Se nenhuma exceção foi atendida, o movimento para a borda é bloqueado.

    if not path_found:
        return "Nenhum caminho encontrado." 
    
    # --- Reconstrução do caminho (sem alterações) ---
    curr: Optional[Coord] = end_tuple
    
    while curr is not None:
        r, c = curr
        matrix[r][c] = 1 
        
        if curr == start_tuple:
             break
        curr = predecessor[r][c]
        
    return matrix