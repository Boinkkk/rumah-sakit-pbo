from __future__ import annotations


class Obat:
    """Entitas Obat dengan enkapsulasi stok dan harga satuan agar tidak bernilai negatif."""

    def __init__(
        self,
        kode_obat: str,
        nama_obat: str,
        stok: int,
        harga_satuan: float,
        satuan: str = "Tablet",
        kategori: str = "Umum",
    ):
        self.__kode_obat = ""
        self.__nama_obat = ""
        self.__stok = 0
        self.__harga_satuan = 0.0
        self.__satuan = "Tablet"
        self.__kategori = "Umum"

        self.set_kode_obat(kode_obat)
        self.set_nama_obat(nama_obat)
        self.set_stok(stok)
        self.set_harga_satuan(harga_satuan)
        self.set_satuan(satuan)
        self.set_kategori(kategori)

    def get_kode_obat(self) -> str:
        return self.__kode_obat

    def set_kode_obat(self, kode_obat: str) -> None:
        if not kode_obat or not kode_obat.strip():
            raise ValueError("Kode obat tidak boleh kosong.")
        self.__kode_obat = kode_obat.strip().upper()

    def get_nama_obat(self) -> str:
        return self.__nama_obat

    def set_nama_obat(self, nama_obat: str) -> None:
        if not nama_obat or not nama_obat.strip():
            raise ValueError("Nama obat tidak boleh kosong.")
        self.__nama_obat = nama_obat.strip()

    def get_stok(self) -> int:
        return self.__stok

    def set_stok(self, stok: int) -> None:
        if stok is None or int(stok) < 0:
            raise ValueError("Stok sediaan obat tidak boleh bernilai negatif.")
        self.__stok = int(stok)

    def kurangi_stok(self, jumlah: int) -> None:
        if jumlah <= 0:
            raise ValueError("Jumlah pengurangan stok harus lebih dari nol.")
        if jumlah > self.__stok:
            raise ValueError(
                f"Stok obat '{self.__nama_obat}' tidak mencukupi (tersedia: {self.__stok}, diminta: {jumlah})."
            )
        self.__stok -= jumlah

    def tambah_stok(self, jumlah: int) -> None:
        if jumlah <= 0:
            raise ValueError("Jumlah penambahan stok harus lebih dari nol.")
        self.__stok += jumlah

    def get_harga_satuan(self) -> float:
        return self.__harga_satuan

    def set_harga_satuan(self, harga_satuan: float) -> None:
        if harga_satuan is None or float(harga_satuan) < 0:
            raise ValueError("Harga satuan obat tidak boleh bernilai negatif.")
        self.__harga_satuan = float(harga_satuan)

    def get_satuan(self) -> str:
        return self.__satuan

    def set_satuan(self, satuan: str) -> None:
        cleaned = (satuan or "").strip()
        self.__satuan = cleaned if cleaned else "Tablet"

    def get_kategori(self) -> str:
        return self.__kategori

    def set_kategori(self, kategori: str) -> None:
        cleaned = (kategori or "").strip()
        self.__kategori = cleaned if cleaned else "Umum"

    def to_dict(self) -> dict:
        return {
            "kode_obat": self.__kode_obat,
            "nama_obat": self.__nama_obat,
            "stok": self.__stok,
            "harga_satuan": self.__harga_satuan,
            "satuan": self.__satuan,
            "kategori": self.__kategori,
        }
