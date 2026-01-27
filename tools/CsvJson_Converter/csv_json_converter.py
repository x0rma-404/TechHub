import csv
import json
from io import StringIO

class CsvJsonConverter:
    def csv_to_json(self, file_stream, delimiter=None):
        text = file_stream.read().decode("utf-8-sig")

        if delimiter in ("", None):
            delimiter = None

        if delimiter:
            reader = csv.DictReader(StringIO(text), delimiter=delimiter)
        else:
            try:
                dialect = csv.Sniffer().sniff(text[:4096], delimiters=[",", ";", "\t", "|"])
                reader = csv.DictReader(StringIO(text), delimiter=dialect.delimiter)
            except Exception:
                reader = csv.DictReader(StringIO(text), delimiter=",")

        if not reader.fieldnames:
            raise ValueError("CSV header not found. First row must contain column names.")

        data = []
        for row in reader:
            if any((v or "").strip() for v in row.values()):
                data.append(row)

        return json.dumps(data, ensure_ascii=False, indent=2)

    def json_to_csv(self, file_stream):
        text = file_stream.read().decode("utf-8")
        data = json.loads(text)

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            raise ValueError("JSON must be an array of objects or a single object.")

        if not data:
            return ""

        fieldnames = []
        seen = set()
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("JSON array must contain only objects.")
            for k in item.keys():
                if k not in seen:
                    seen.add(k)
                    fieldnames.append(k)

        out = StringIO()
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

        return out.getvalue()
