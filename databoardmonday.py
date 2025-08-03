import requests
import json
from typing import Dict, List, Optional

class MondayClient:
    def __init__(self, api_token: str):
        """
        Inicializa el cliente de Monday.com
        
        Args:
            api_token: Token de API de Monday.com
        """
        self.api_token = api_token
        self.api_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json"
        }
    
    def execute_query(self, query: str, variables: Dict = None) -> Dict:
        """
        Ejecuta una consulta GraphQL en Monday.com
        
        Args:
            query: Consulta GraphQL
            variables: Variables para la consulta
            
        Returns:
            Respuesta de la API
        """
        data = {"query": query}
        if variables:
            data["variables"] = variables
            
        response = requests.post(
            self.api_url,
            json=data,
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error en la API: {response.status_code} - {response.text}")
    
    def get_boards(self) -> List[Dict]:
        """
        Obtiene todos los tableros disponibles
        
        Returns:
            Lista de tableros
        """
        query = """
        query {
            boards {
                id
                name
                description
                state
            }
        }
        """
        
        result = self.execute_query(query)
        return result.get("data", {}).get("boards", [])
    
    def get_board_columns(self, board_id: str) -> List[Dict]:
        """
        Obtiene las columnas de un tablero específico
        
        Args:
            board_id: ID del tablero
            
        Returns:
            Lista de columnas del tablero
        """
        query = """
        query ($board_id: [ID!]) {
            boards(ids: $board_id) {
                columns {
                    id
                    title
                    type
                    settings_str
                }
            }
        }
        """
        
        variables = {"board_id": [board_id]}
        result = self.execute_query(query, variables)
        
        boards = result.get("data", {}).get("boards", [])
        if boards:
            return boards[0].get("columns", [])
        return []
    
    def get_board_items(self, board_id: str, limit: int = 100) -> List[Dict]:
        """
        Obtiene los elementos (filas) de un tablero con todos sus valores
        
        Args:
            board_id: ID del tablero
            limit: Límite de elementos a obtener
            
        Returns:
            Lista de elementos del tablero
        """
        query = """
        query ($board_id: [ID!], $limit: Int) {
            boards(ids: $board_id) {
                items_page(limit: $limit) {
                    items {
                        id
                        name
                        state
                        created_at
                        updated_at
                        column_values {
                            id
                            type
                            text
                            value
                        }
                    }
                }
            }
        }
        """
        
        variables = {"board_id": [board_id], "limit": limit}
        result = self.execute_query(query, variables)
        
        boards = result.get("data", {}).get("boards", [])
        if boards and boards[0].get("items_page"):
            return boards[0]["items_page"].get("items", [])
        return []
    
    def create_column_mapping(self, columns: List[Dict]) -> Dict[str, str]:
        """
        Crea un mapeo de ID de columna a título de columna
        
        Args:
            columns: Lista de columnas del tablero
            
        Returns:
            Diccionario {column_id: column_title}
        """
        return {col["id"]: col["title"] for col in columns}
    
    def get_board_data_formatted(self, board_id: str) -> Dict:
        """
        Obtiene datos completos del tablero en formato estructurado
        
        Args:
            board_id: ID del tablero
            
        Returns:
            Diccionario con información completa del tablero
        """
        # Obtener información del tablero
        board_query = """
        query ($board_id: [ID!]) {
            boards(ids: $board_id) {
                id
                name
                description
                state
                columns {
                    id
                    title
                    type
                    settings_str
                }
                items_page(limit: 100) {
                    items {
                        id
                        name
                        state
                        created_at
                        updated_at
                        column_values {
                            id
                            type
                            text
                            value
                        }
                    }
                }
            }
        }
        """
        
        variables = {"board_id": [board_id]}
        result = self.execute_query(board_query, variables)
        
        boards = result.get("data", {}).get("boards", [])
        if not boards:
            return {}
        
        board = boards[0]
        columns = board.get("columns", [])
        
        # Crear mapeo de columnas (ID -> Título)
        column_mapping = self.create_column_mapping(columns)
        
        # Formatear datos
        formatted_data = {
            "board_info": {
                "id": board.get("id"),
                "name": board.get("name"),
                "description": board.get("description"),
                "state": board.get("state")
            },
            "columns": columns,
            "column_mapping": column_mapping,
            "items": []
        }
        
        # Procesar elementos
        items = board.get("items_page", {}).get("items", [])
        for item in items:
            formatted_item = {
                "id": item.get("id"),
                "name": item.get("name"),
                "state": item.get("state"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "column_data": {}
            }
            
            # Organizar valores de columnas usando el mapeo
            for col_value in item.get("column_values", []):
                column_id = col_value.get("id")
                column_title = column_mapping.get(column_id, f"Columna_{column_id}")
                
                formatted_item["column_data"][column_title] = {
                    "column_id": column_id,
                    "type": col_value.get("type"),
                    "text": col_value.get("text"),
                    "raw_value": col_value.get("value")
                }
            
            formatted_data["items"].append(formatted_item)
        
        return formatted_data
    
    def export_to_csv(self, board_data: Dict, filename: str = None) -> str:
        """
        Exporta los datos del tablero a CSV
        
        Args:
            board_data: Datos del tablero obtenidos con get_board_data_formatted
            filename: Nombre del archivo (opcional)
            
        Returns:
            Nombre del archivo creado
        """
        if not filename:
            board_name = board_data.get("board_info", {}).get("name", "tablero")
            filename = f"monday_{board_name.replace(' ', '_')}.csv"
        
        import csv
        
        if not board_data.get("items"):
            print("No hay elementos para exportar")
            return filename
        
        # Obtener todas las columnas únicas
        all_columns = set()
        for item in board_data["items"]:
            all_columns.update(item["column_data"].keys())
        
        all_columns = sorted(list(all_columns))
        
        # Escribir CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ID', 'Nombre', 'Estado', 'Creado', 'Actualizado'] + all_columns
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for item in board_data["items"]:
                row = {
                    'ID': item['id'],
                    'Nombre': item['name'],
                    'Estado': item['state'],
                    'Creado': item['created_at'],
                    'Actualizado': item['updated_at']
                }
                
                # Agregar datos de columnas
                for col_name in all_columns:
                    col_data = item["column_data"].get(col_name, {})
                    row[col_name] = col_data.get("text", "")
                
                writer.writerow(row)
        
        return filename

def main():
    """
    Función principal para demostrar el uso del script
    """
    # Configuración
    API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUyMjMzNzU5MywiYWFpIjoxMSwidWlkIjo3NDMxODI5OCwiaWFkIjoiMjAyNS0wNi0wNVQwNjowNToxNC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjMwNjk5OSwicmduIjoidXNlMSJ9.t5ZeM_lS9OhTXymRiYaB0CLjY4AFo60n5dabiSxSpvk"  # Reemplaza con tu token
    BOARD_ID = "8700483524"       # Reemplaza con el ID de tu tablero
    
    try:
        # Inicializar cliente
        client = MondayClient(API_TOKEN)
        
        # Obtener lista de tableros
        print("=== TABLEROS DISPONIBLES ===")
        boards = client.get_boards()
        for board in boards[:5]:  # Mostrar solo los primeros 5
            print(f"ID: {board['id']} - Nombre: {board['name']}")
        
        print(f"\n=== DATOS DEL TABLERO {BOARD_ID} ===")
        
        # Obtener datos completos del tablero
        board_data = client.get_board_data_formatted(BOARD_ID)
        
        if board_data:
            # Mostrar información del tablero
            print(f"Tablero: {board_data['board_info']['name']}")
            print(f"Descripción: {board_data['board_info']['description']}")
            
            # Mostrar columnas
            print(f"\n=== COLUMNAS ({len(board_data['columns'])}) ===")
            for col in board_data['columns']:
                print(f"- {col['title']} (ID: {col['id']}, Tipo: {col['type']})")
            
            # Mostrar elementos
            print(f"\n=== ELEMENTOS ({len(board_data['items'])}) ===")
            for item in board_data['items'][:3]:  # Mostrar solo los primeros 3
                print(f"\nElemento: {item['name']} (ID: {item['id']})")
                print(f"Estado: {item['state']}")
                print("Datos de columnas:")
                for col_name, col_data in item['column_data'].items():
                    if col_data['text']:  # Solo mostrar si tiene valor
                        print(f"  - {col_name}: {col_data['text']}")
            
            # Guardar datos en archivo JSON
            json_filename = f"monday_board_{BOARD_ID}.json"
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(board_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Datos JSON guardados en {json_filename}")
            
            # Exportar a CSV
            csv_filename = client.export_to_csv(board_data)
            print(f"✅ Datos CSV guardados en {csv_filename}")
            
        else:
            print("❌ No se pudieron obtener datos del tablero")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# Función adicional para obtener datos específicos de una columna
def get_column_data(client: MondayClient, board_id: str, column_name: str) -> List[Dict]:
    """
    Obtiene datos específicos de una columna
    
    Args:
        client: Cliente de Monday
        board_id: ID del tablero
        column_name: Nombre de la columna
        
    Returns:
        Lista con los datos de la columna
    """
    board_data = client.get_board_data_formatted(board_id)
    column_data = []
    
    for item in board_data.get("items", []):
        if column_name in item["column_data"]:
            column_data.append({
                "item_name": item["name"],
                "item_id": item["id"],
                "column_value": item["column_data"][column_name]["text"],
                "raw_value": item["column_data"][column_name]["raw_value"]
            })
    
    return column_data

if __name__ == "__main__":
    main()